"""Unit tests never depend on production mailbox credentials."""
import os
os.environ.setdefault('HSB_COM_JOEL_USER','m0821e5d')
os.environ.setdefault('HSB_COM_JORDI_USER','m0821e5b')
os.environ.setdefault('HSB_COM_JOEL_PASS','unit-test-password')
os.environ.setdefault('HSB_COM_JORDI_PASS','unit-test-password')
