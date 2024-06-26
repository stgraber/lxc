/* liblxcapi
 *
 * SPDX-License-Identifier: GPL-2.0-only
 *
 */

#include "config.h"

#include <errno.h>
#include <string.h>
#include <unistd.h>
#include <sys/stat.h>
#include <sys/syscall.h>
#include <sys/types.h>

#include "lxctest.h"
#include "utils.h"
#include "lsm/lsm.h"

#include <lxc/lxccontainer.h>

#if !HAVE_STRLCPY
#include "strlcpy.h"
#endif

#define TSTNAME    "lxc-attach-test"
#define TSTOUT(fmt, ...) do { \
	fprintf(stdout, fmt, ##__VA_ARGS__); fflush(NULL); \
} while (0)
#define TSTERR(fmt, ...) do { \
	fprintf(stderr, "%s:%d " fmt "\n", __FILE__, __LINE__, ##__VA_ARGS__); fflush(NULL); \
} while (0)

static const char *lsm_config_key = NULL;
static const char *lsm_label = NULL;

struct lsm_ops *lsm_ops;

static void test_lsm_detect(void)
{
	if (lsm_ops->enabled(lsm_ops)) {
		if (!strcmp(lsm_ops->name, "SELinux")) {
			lsm_config_key = "lxc.selinux.context";
			lsm_label      = "unconfined_u:unconfined_r:lxc_t:s0-s0:c0.c1023";
		}
		else if (!strcmp(lsm_ops->name, "AppArmor")) {
			lsm_config_key = "lxc.apparmor.profile";
			if (file_exists("/proc/self/ns/cgroup"))
				lsm_label      = "lxc-container-default-cgns";
			else
				lsm_label      = "lxc-container-default";
		}
		else {
			TSTERR("unknown lsm %s enabled, add test code here", lsm_ops->name);
			exit(EXIT_FAILURE);
		}
	}
}

#if HAVE_APPARMOR || HAVE_SELINUX
static void test_attach_lsm_set_config(struct lxc_container *ct)
{
	ct->load_config(ct, NULL);
	ct->set_config_item(ct, lsm_config_key, lsm_label);
	ct->save_config(ct, NULL);
}

static int test_attach_lsm_func_func(void* payload)
{
	TSTOUT("%s", lsm_ops->process_label_get(lsm_ops, syscall(SYS_getpid)));
	return 0;
}

static int test_attach_lsm_func(struct lxc_container *ct)
{
	int ret;
	pid_t pid;
	int pipefd[2];
	char result[1024];
	lxc_attach_options_t attach_options = LXC_ATTACH_OPTIONS_DEFAULT;

	TSTOUT("Testing attach lsm label with func...\n");

	ret = pipe(pipefd);
	if (ret < 0) {
		TSTERR("pipe failed %d", ret);
		return ret;
	}
	attach_options.stdout_fd = pipefd[1];
	attach_options.attach_flags &= ~(LXC_ATTACH_LSM_EXEC|LXC_ATTACH_DROP_CAPABILITIES);
	attach_options.attach_flags |= LXC_ATTACH_LSM_NOW;
	ret = ct->attach(ct, test_attach_lsm_func_func, NULL, &attach_options, &pid);
	if (ret < 0) {
		TSTERR("attach failed");
		goto err1;
	}

	ret = read(pipefd[0], result, sizeof(result)-1);
	if (ret < 0) {
		TSTERR("read failed %d", ret);
		goto err2;
	}

	result[ret] = '\0';
	if (strcmp(lsm_label, result)) {
		TSTERR("LSM label mismatch expected:%s got:%s", lsm_label, result);
		ret = -1;
		goto err2;
	}
	ret = 0;

err2:
	(void)wait_for_pid(pid);
err1:
	close(pipefd[0]);
	close(pipefd[1]);
	return ret;
}

static int test_attach_lsm_cmd(struct lxc_container *ct)
{
	int ret;
	pid_t pid;
	int pipefd[2];
	char result[1024];
	char *space;
	char *argv[] = {"cat", "/proc/self/attr/current", NULL};
	lxc_attach_command_t command = {"cat", argv};
	lxc_attach_options_t attach_options = LXC_ATTACH_OPTIONS_DEFAULT;

	TSTOUT("Testing attach lsm label with cmd...\n");

	ret = pipe(pipefd);
	if (ret < 0) {
		TSTERR("pipe failed %d", ret);
		return ret;
	}
	attach_options.stdout_fd = pipefd[1];

	ret = ct->attach(ct, lxc_attach_run_command, &command, &attach_options, &pid);
	if (ret < 0) {
		TSTERR("attach failed");
		goto err1;
	}

	ret = read(pipefd[0], result, sizeof(result)-1);
	if (ret < 0) {
		TSTERR("read failed %d", ret);
		goto err2;
	}
	result[ret] = '\0';
	space = strchr(result, '\n');
	if (space)
		*space = '\0';
	space = strchr(result, ' ');
	if (space)
		*space = '\0';

	ret = -1;
	if (strcmp(lsm_label, result)) {
		TSTERR("LSM label mismatch expected:%s got:%s", lsm_label, result);
		goto err2;
	}
	ret = 0;

err2:
	(void)wait_for_pid(pid);
err1:
	close(pipefd[0]);
	close(pipefd[1]);
	return ret;
}
#else
static void test_attach_lsm_set_config(struct lxc_container *ct) {}
static int  test_attach_lsm_func(struct lxc_container *ct) { return 0; }
static int  test_attach_lsm_cmd(struct lxc_container *ct) { return 0; }
#endif /* HAVE_APPARMOR || HAVE_SELINUX */

static int test_attach_func_func(void* payload)
{
	TSTOUT("%d", (int)syscall(SYS_getpid));
	return 0;
}

static int test_attach_func(struct lxc_container *ct)
{
	int ret;
	pid_t pid,nspid;
	int pipefd[2];
	char result[1024];
	lxc_attach_options_t attach_options = LXC_ATTACH_OPTIONS_DEFAULT;

	TSTOUT("Testing attach with func...\n");

	/* XXX: We can't just use &nspid and have test_attach_func_func fill
	 * it in because the function doesn't run in our process context but
	 * in a fork()ed from us context. We read the result through a pipe.
	 */
	ret = pipe(pipefd);
	if (ret < 0) {
		TSTERR("pipe failed %d", ret);
		return ret;
	}
	attach_options.stdout_fd = pipefd[1];

	ret = ct->attach(ct, test_attach_func_func, NULL, &attach_options, &pid);
	if (ret < 0) {
		TSTERR("attach failed");
		goto err1;
	}

	ret = read(pipefd[0], result, sizeof(result)-1);
	if (ret < 0) {
		TSTERR("read failed %d", ret);
		goto err2;
	}
	result[ret] = '\0';

	/* There is a small chance the pid is reused inside the NS, so we
	 * just print it and don't actually do this check
	 *
	 * if (pid == nspid) TSTERR(...)
	 */
	nspid = atoi(result);
	TSTOUT("Pid:%d in NS:%d\n", pid, nspid);
	ret = 0;

err2:
	(void)wait_for_pid(pid);
err1:
	close(pipefd[0]);
	close(pipefd[1]);
	return ret;
}

static int test_attach_cmd(struct lxc_container *ct)
{
	int ret;
	pid_t pid;
	char *argv[] = {"cmp", "-s", "/sbin/init", "/bin/busybox", NULL};
	lxc_attach_command_t command = {"cmp", argv};
	lxc_attach_options_t attach_options = LXC_ATTACH_OPTIONS_DEFAULT;

	TSTOUT("Testing attach with success command...\n");
	ret = ct->attach(ct, lxc_attach_run_command, &command, &attach_options, &pid);
	if (ret < 0) {
		TSTERR("attach failed");
		return ret;
	}

	ret = wait_for_pid(pid);
	if (ret < 0) {
		TSTERR("attach success command got bad return %d", ret);
		return ret;
	}

	TSTOUT("Testing attach with failure command...\n");
	argv[2] = "/etc/fstab";
	ret = ct->attach(ct, lxc_attach_run_command, &command, &attach_options, &pid);
	if (ret < 0) {
		TSTERR("attach failed");
		return ret;
	}

	ret = wait_for_pid(pid);
	if (ret == 0) {
		TSTERR("attach failure command got bad return %d", ret);
		return -1;
	}
	return 0;
}

/* test_ct_destroy: stop and destroy the test container
 *
 * @ct       : the container
 */
static void test_ct_destroy(struct lxc_container *ct)
{
	ct->stop(ct);
	ct->destroy(ct);
	lxc_container_put(ct);
}

/* test_ct_create: create and start test container
 *
 * @lxcpath  : the lxcpath in which to create the container
 * @group    : name of the container group or NULL for default "lxc"
 * @name     : name of the container
 * @template : template to use when creating the container
 */
static struct lxc_container *test_ct_create(const char *lxcpath,
				const char *group, const char *name,
				const char *template)
{
	int ret;
	struct lxc_container *ct = NULL;

	if (lxcpath) {
		ret = mkdir(lxcpath, 0755);
		if (ret < 0 && errno != EEXIST) {
			TSTERR("failed to mkdir %s %s", lxcpath, strerror(errno));
			goto out1;
		}
	}

	if ((ct = lxc_container_new(name, lxcpath)) == NULL) {
		TSTERR("instantiating container %s", name);
		goto out1;
	}
	if (ct->is_defined(ct)) {
		test_ct_destroy(ct);
		ct = lxc_container_new(name, lxcpath);
	}
	if (!ct->createl(ct, template, NULL, NULL, 0, NULL)) {
		TSTERR("creating container %s", name);
		goto out2;
	}

	if (lsm_ops->enabled(lsm_ops))
		test_attach_lsm_set_config(ct);

	ct->want_daemonize(ct, true);
	if (!ct->startl(ct, 0, NULL)) {
		TSTERR("starting container %s", name);
		goto out2;
	}
	return ct;

out2:
	test_ct_destroy(ct);
	ct = NULL;
out1:
	return ct;
}


static int test_attach(const char *lxcpath, const char *name, const char *template)
{
	int ret = -1;
	struct lxc_container *ct;

	TSTOUT("Testing attach with on lxcpath:%s\n", lxcpath ? lxcpath : "<default>");
	ct = test_ct_create(lxcpath, NULL, name, template);
	if (!ct)
		goto err1;

	ret = test_attach_cmd(ct);
	if (ret < 0) {
		TSTERR("attach cmd test failed");
		goto err2;
	}

	ret = test_attach_func(ct);
	if (ret < 0) {
		TSTERR("attach func test failed");
		goto err2;
	}

	if (lsm_ops->enabled(lsm_ops)) {
		ret = test_attach_lsm_cmd(ct);
		if (ret < 0) {
			TSTERR("attach lsm cmd test failed");
			goto err2;
		}

		ret = test_attach_lsm_func(ct);
		if (ret < 0) {
			TSTERR("attach lsm func test failed");
			goto err2;
		}
	}
	ret = 0;

err2:
	test_ct_destroy(ct);
err1:
	return ret;
}

int main(int argc, char *argv[])
{
	int i, ret;
	struct lxc_log log;
	char template[sizeof(P_tmpdir"/attach_XXXXXX")];
	int fret = EXIT_FAILURE;

	(void)strlcpy(template, P_tmpdir"/attach_XXXXXX", sizeof(template));

	lsm_ops = lsm_init_static();

	i = lxc_make_tmpfile(template, false);
	if (i < 0) {
		lxc_error("Failed to create temporary log file for container %s\n", TSTNAME);
		exit(EXIT_FAILURE);
	} else {
		lxc_debug("Using \"%s\" as temporary log file for container %s\n", template, TSTNAME);
		close(i);
	}

	log.name = TSTNAME;
	log.file = template;
	log.level = "TRACE";
	log.prefix = "attach";
	log.quiet = false;
	log.lxcpath = NULL;
	if (lxc_log_init(&log))
		goto on_error;

	test_lsm_detect();
	ret = test_attach(NULL, TSTNAME, "busybox");
	if (ret < 0)
		goto on_error;

	TSTOUT("\n");
	ret = test_attach(LXCPATH "/alternate-path-test", TSTNAME, "busybox");
	if (ret < 0)
		goto on_error;

	TSTOUT("All tests passed\n");
	fret = EXIT_SUCCESS;

on_error:
	if (fret != EXIT_SUCCESS) {
		int fd;

		fd = open(template, O_RDONLY);
		if (fd >= 0) {
			char buf[4096];
			ssize_t buflen;
			while ((buflen = read(fd, buf, 1024)) > 0) {
				buflen = write(STDERR_FILENO, buf, buflen);
				if (buflen <= 0)
					break;
			}
			close(fd);
		}
	}
	(void)rmdir(LXCPATH "/alternate-path-test");
	(void)unlink(template);
	exit(fret);
}
