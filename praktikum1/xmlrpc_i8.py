"""Dukungan ``<i8>`` untuk pengujian integer besar pada L1.3.

XML-RPC standar mendefinisikan ``<int>`` sebagai signed 32-bit. Marshaller
bawaan Python menolak nilai di luar rentang itu sebelum request dikirim,
sedangkan Unmarshaller bawaan sudah mengenali ``<i8>``. Modul ini menambahkan
marshaller dan server dispatcher minimal agar nilai seperti ``2**31 + 1`` dapat
dikirim dan dikembalikan sebagai ``int`` tanpa kehilangan nilai atau tipe.
"""

from __future__ import annotations

import xmlrpc.client
from xmlrpc.client import Fault, escape
from xmlrpc.server import SimpleXMLRPCServer

INT32_MIN = -(2**31)
INT32_MAX = 2**31 - 1
INT64_MIN = -(2**63)
INT64_MAX = 2**63 - 1


class I8Marshaller(xmlrpc.client.Marshaller):
    """Marshaller yang memakai ``<i8>`` untuk int di luar signed 32-bit."""

    dispatch = xmlrpc.client.Marshaller.dispatch.copy()

    def dump_long(self, value: int, write) -> None:
        if INT32_MIN <= value <= INT32_MAX:
            super().dump_long(value, write)
            return
        if not INT64_MIN <= value <= INT64_MAX:
            raise OverflowError("int exceeds XML-RPC i8 limits")
        write("<value><i8>")
        write(str(int(value)))
        write("</i8></value>\n")


I8Marshaller.dispatch[int] = I8Marshaller.dump_long


def dumps_i8(
    params,
    methodname: str | None = None,
    methodresponse: bool = False,
    encoding: str = "utf-8",
    allow_none: bool = False,
) -> str:
    """Membuat XML request/response dengan dukungan ``<i8>``."""
    marshaller = I8Marshaller(encoding, allow_none)
    data = marshaller.dumps(params)

    if encoding != "utf-8":
        xml_header = f"<?xml version='1.0' encoding='{encoding}'?>\n"
    else:
        xml_header = "<?xml version='1.0'?>\n"

    if methodname:
        return (
            xml_header
            + "<methodCall>\n"
            + "<methodName>"
            + escape(methodname)
            + "</methodName>\n"
            + data
            + "</methodCall>\n"
        )
    if methodresponse:
        return xml_header + "<methodResponse>\n" + data + "</methodResponse>\n"
    return data


class I8ServerProxy(xmlrpc.client.ServerProxy):
    """ServerProxy yang mengirim int besar sebagai ``<i8>``."""

    def _ServerProxy__request(self, methodname: str, params: tuple):
        request = dumps_i8(
            params,
            methodname,
            encoding=self._ServerProxy__encoding,
            allow_none=self._ServerProxy__allow_none,
        ).encode(self._ServerProxy__encoding, "xmlcharrefreplace")
        response = self._ServerProxy__transport.request(
            self._ServerProxy__host,
            self._ServerProxy__handler,
            request,
            verbose=self._ServerProxy__verbose,
        )
        if len(response) == 1:
            response = response[0]
        return response


class I8XMLRPCServer(SimpleXMLRPCServer):
    """SimpleXMLRPCServer yang membalas int besar dengan ``<i8>``."""

    def _marshaled_dispatch(self, data, dispatch_method=None, path=None):
        try:
            params, method = xmlrpc.client.loads(
                data, use_builtin_types=self.use_builtin_types
            )
            if dispatch_method is not None:
                response = dispatch_method(method, params)
            else:
                response = self._dispatch(method, params)
            response_xml = dumps_i8(
                (response,),
                methodresponse=True,
                allow_none=self.allow_none,
                encoding=self.encoding,
            )
        except Fault as fault:
            response_xml = dumps_i8(
                fault,
                allow_none=self.allow_none,
                encoding=self.encoding,
            )
        except BaseException as exc:
            response_xml = dumps_i8(
                Fault(1, f"{type(exc)}:{exc}"),
                allow_none=self.allow_none,
                encoding=self.encoding,
            )
        return response_xml.encode(self.encoding, "xmlcharrefreplace")
