# -*- coding: utf-8 -*-
#
# lxc: New LXC command line client
#
# Authors:
# Stephane Graber <stgraber@ubuntu.com> (Canonical Ltd. 2014)
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA

# Import everything we need
import glob
import hashlib
import logging
import os
import ssl
import subprocess

from lxccmd.config import get_config_path


def generate_cert(cert_type):
    """
        Generate a new X509 certificate if needed.
    """

    cert_path = os.path.join(get_config_path(), "certs")
    if not os.path.exists(cert_path):
        os.makedirs(cert_path)

    if not os.path.exists(os.path.join(cert_path, "%s.key" % cert_type)) or \
            not os.path.exists(os.path.join(cert_path, "%s.crt" % cert_type)):
        with open(os.devnull, "w") as devnull:
            if subprocess.call(["openssl", "req", "-new",
                                "-newkey", "rsa:4096",
                                "-days", "3650",
                                "-nodes", "-x509",
                                "-subj", "/CN=LXC server certificate",
                                "-keyout", os.path.join(cert_path, "%s.key"
                                                        % cert_type),
                                "-out", os.path.join(cert_path, "%s.crt"
                                                     % cert_type)],
                               stdout=devnull, stderr=devnull) == 0:
                ca_path = os.path.join(cert_path, "%s-ca" % cert_type)
                if not os.path.exists(ca_path):
                    os.mkdir(ca_path)
                return True
    return False


def get_cert_path(cert_type):
    """
        Return a tuple of the paths for the certificate, key and ca file.
    """

    cert_path = os.path.join(get_config_path(), "certs")

    return (os.path.join(cert_path, "%s.crt" % cert_type),
            os.path.join(cert_path, "%s.key" % cert_type),
            os.path.join(cert_path, "%s-ca/" % cert_type))


def get_fingerprint(cert_type):
    """
        Return the SHA-1 fingerprint of the certificate.
    """

    cert_path = os.path.join(get_config_path(), "certs")

    if not os.path.exists(os.path.join(cert_path, "%s.crt" % cert_type)):
        return False

    with open(os.path.join(cert_path, "%s.crt" % cert_type), "r") as fd:
        return hashlib.sha1(ssl.PEM_cert_to_DER_cert(fd.read())).hexdigest()


def trust_cert_add(x509_cert, trust_store):
    """
        Adds a certificate to the trust store.
    """

    try:
        fingerprint = hashlib.sha1(
            ssl.PEM_cert_to_DER_cert(x509_cert)).hexdigest()
    except:
        logging.error("Invalid x509 certificate.")
        return False

    store = get_cert_path(trust_store)[2]

    with open(os.path.join(store, "%s.crt" % fingerprint), "w+") as fd:
        fd.write(x509_cert)

    with open(os.devnull, "w") as devnull:
        if subprocess.call(["c_rehash", store], stdout=devnull) != 0:
            logging.error("Failed to re-hash the store.")
            return False

    return True


def trust_cert_list(trust_store):
    """
        Returns a list of trusted certificate fingerprints.
    """

    store = get_cert_path(trust_store)[2]
    certs = []
    for entry in glob.glob("%s/*.crt" % store):
        certs.append(os.path.basename(entry.split(".crt")[0]))
    return certs


def trust_cert_remove(x509_cert, trust_store):
    """
        Remove a certificate from the trust store.
        The certificate can be either a x509 certificate or a hash.
    """

    try:
        fingerprint = hashlib.sha1(
            ssl.PEM_cert_to_DER_cert(x509_cert)).hexdigest()
    except:
        fingerprint = x509_cert

    store = get_cert_path(trust_store)[2]

    if not os.path.exists(os.path.join(store, "%s.crt" % fingerprint)):
        return False

    os.remove(os.path.join(store, "%s.crt" % fingerprint))

    with open(os.devnull, "w") as devnull:
        if subprocess.call(["c_rehash", store], stdout=devnull) != 0:
            logging.error("Failed to re-hash the store.")
            return False

    return True
