/* SPDX-License-Identifier: GPL-2.0-only */

#include "config.h"

#include <ctype.h>
#include <fcntl.h>
#include <libgen.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/types.h>
#include <unistd.h>

#include "lxc.h"

#include "arguments.h"
#include "log.h"

lxc_log_define(lxc_snapshot, lxc);

static int my_parser(struct lxc_arguments *args, int c, char *arg);

static const struct option my_longopts[] = {
	{"list", no_argument, 0, 'L'},
	{"restore", required_argument, 0, 'r'},
	{"newname", required_argument, 0, 'N'},
	{"destroy", required_argument, 0, 'd'},
	{"comment", required_argument, 0, 'c'},
	{"showcomments", no_argument, 0, 'C'},
	LXC_COMMON_OPTIONS
};

static struct lxc_arguments my_args = {
	.progname = "lxc-snapshot",
	.help = "\
--name=NAME [-P lxcpath] [-L [-C]] [-c commentfile] [-r snapname [-N newname]]\n\
\n\
lxc-snapshot snapshots a container\n\
\n\
Options :\n\
  -n, --name=NAME        NAME of the container\n\
  -L, --list             list all snapshots\n\
  -r, --restore=NAME     restore snapshot NAME, e.g. 'snap0'\n\
  -N, --newname=NEWNAME  NEWNAME for the restored container\n\
  -d, --destroy=NAME     destroy snapshot NAME, e.g. 'snap0'\n\
                         use ALL to destroy all snapshots\n\
  -c, --comment=FILE     add FILE as a comment\n\
  -C, --showcomments     show snapshot comments\n\
  --rcfile=FILE          Load configuration file FILE\n",
	.options = my_longopts,
	.parser = my_parser,
	.checker = NULL,
	.task = SNAP,
	.log_priority = "ERROR",
	.log_file     = "none",
};

static int do_snapshot(struct lxc_container *c, char *commentfile);
static int do_snapshot_destroy(struct lxc_container *c, char *snapname);
static int do_snapshot_list(struct lxc_container *c, int print_comments);
static int do_snapshot_restore(struct lxc_container *c,
			       struct lxc_arguments *args);
static int do_snapshot_task(struct lxc_container *c, enum task task);
static void print_file(char *path);

int __attribute__((weak, alias("lxc_snapshot_main"))) main(int argc, char *argv[]);
int lxc_snapshot_main(int argc, char *argv[])
{
	struct lxc_container *c;
	struct lxc_log log;
	int ret;

	if (lxc_arguments_parse(&my_args, argc, argv))
		exit(EXIT_FAILURE);

	/* Only create log if explicitly instructed */
	if (my_args.log_file || my_args.log_priority) {
		log.name = my_args.name;
		log.file = my_args.log_file;
		log.level = my_args.log_priority;
		log.prefix = my_args.progname;
		log.quiet = my_args.quiet;
		log.lxcpath = my_args.lxcpath[0];

		if (lxc_log_init(&log))
			exit(EXIT_FAILURE);
	}

	if (geteuid()) {
		if (access(my_args.lxcpath[0], O_RDONLY) < 0) {
			ERROR("You lack access to %s", my_args.lxcpath[0]);
			exit(EXIT_FAILURE);
		}
	}

	c = lxc_container_new(my_args.name, my_args.lxcpath[0]);
	if (!c) {
		ERROR("System error loading container");
		exit(EXIT_FAILURE);
	}

	if (my_args.rcfile) {
		c->clear_config(c);

		if (!c->load_config(c, my_args.rcfile)) {
			ERROR("Failed to load rcfile");
			lxc_container_put(c);
			exit(EXIT_FAILURE);
		}

		c->configfile = strdup(my_args.rcfile);
		if (!c->configfile) {
			ERROR("Out of memory setting new config filename");
			lxc_container_put(c);
			exit(EXIT_FAILURE);
		}
	}

	if (!c->lxc_conf) {
		ERROR("No container config specified");
		lxc_container_put(c);
		exit(EXIT_FAILURE);
	}

	if (!c->may_control(c)) {
		ERROR("Insufficent privileges to control %s", my_args.name);
		lxc_container_put(c);
		exit(EXIT_FAILURE);
	}

	ret = do_snapshot_task(c, my_args.task);

	lxc_container_put(c);

	if (ret == 0)
		exit(EXIT_SUCCESS);

	exit(EXIT_FAILURE);
}

static int do_snapshot_task(struct lxc_container *c, enum task task)
{
	int ret = 0;

	switch (task) {
	case DESTROY:
		ret = do_snapshot_destroy(c, my_args.snapname);
		break;
	case LIST:
		ret = do_snapshot_list(c, my_args.print_comments);
		break;
	case RESTORE:
		ret = do_snapshot_restore(c, &my_args);
		break;
	case SNAP:
		ret = do_snapshot(c, my_args.commentfile);
		break;
	default:
		ret = 0;
		break;
	}

	return ret;
}

static int my_parser(struct lxc_arguments *args, int c, char *arg)
{
	switch (c) {
	case 'L':
		args->task = LIST;
		break;
	case 'r':
		args->task = RESTORE;
		args->snapname = arg;
		break;
	case 'N':
		args->newname = arg;
		break;
	case 'd':
		args->task = DESTROY;
		args->snapname = arg;
		break;
	case 'c':
		args->commentfile = arg;
		break;
	case 'C':
		args->print_comments = 1;
		break;
	}

	return 0;
}

static int do_snapshot(struct lxc_container *c, char *commentfile)
{
	int ret;

	ret = c->snapshot(c, commentfile);
	if (ret < 0) {
		ERROR("Error creating a snapshot");
		return -1;
	}

	return 0;
}

static int do_snapshot_destroy(struct lxc_container *c, char *snapname)
{
	bool ret;

	if (strncmp(snapname, "ALL", strlen(snapname)) == 0)
		ret = c->snapshot_destroy_all(c);
	else
		ret = c->snapshot_destroy(c, snapname);

	if (!ret) {
		ERROR("Error destroying snapshot %s", snapname);
		return -1;
	}

	return 0;
}

static int do_snapshot_list(struct lxc_container *c, int print_comments)
{
	struct lxc_snapshot *s;
	int i, n;

	n = c->snapshot_list(c, &s);
	if (n < 0) {
		ERROR("Error listing snapshots");
		return -1;
	}

	if (n == 0) {
		printf("No snapshots\n");
		return 0;
	}

	for (i = 0; i < n; i++) {
		printf("%s (%s) %s\n", s[i].name, s[i].lxcpath, s[i].timestamp);

		if (print_comments)
			print_file(s[i].comment_pathname);

		s[i].free(&s[i]);
	}

	free(s);

	return 0;
}

static int do_snapshot_restore(struct lxc_container *c,
			       struct lxc_arguments *args)
{
	int bret;

	/* When restoring  a snapshot, the last optional argument if not given
	 * explicitly via the corresponding command line option is the name to
	 * use for the restored container. If no name is given, then the
	 * original container will be destroyed and the restored container will
	 * take its place. */
	if ((!args->newname) && (args->argc > 1)) {
		ERROR("Too many arguments");
		return -1;
	}

	if ((!args->newname) && (args->argc == 1))
		args->newname = args->argv[0];

	bret = c->snapshot_restore(c, args->snapname, args->newname);
	if (!bret) {
		ERROR("Error restoring snapshot %s", args->snapname);
		return -1;
	}

	return 0;
}

static void print_file(char *path)
{
	FILE *f;
	char *line = NULL;
	size_t sz = 0;

	if (!path)
		return;

	f = fopen(path, "r");
	if (!f)
		return;

	while (getline(&line, &sz, f) != -1)
		printf("%s", line);

	free(line);
	fclose(f);
}
