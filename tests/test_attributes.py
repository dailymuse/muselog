import unittest

from muselog import attributes

from .support import ClearContext


class NetworkAttributesTestCase(ClearContext, unittest.TestCase):

    def test_standardize_forward_header_priority(self):
        headers = {
            "True-Client-Ip": "123.22.11.59",
            "Forwarded": "12.22.11.50,54.56.129.12",
            "X-Forwarded-For": "90.32.53.8,12.22.11.50,54.56.129.12"
        }
        network_attrs = attributes.NetworkAttributes(extract_header=headers.get, remote_addr="99.58.39.5")
        result = network_attrs.standardize()

        # Prefer cloudflare if available
        self.assertEqual(result["network.client.ip"], "123.22.11.59")

        del headers["True-Client-Ip"]

        network_attrs = attributes.NetworkAttributes(extract_header=headers.get, remote_addr="99.58.39.5")
        result = network_attrs.standardize()

        # Prefer Forwarded if cloudflare unavailable
        self.assertEqual(result["network.client.ip"], "12.22.11.50")

        del headers["Forwarded"]

        network_attrs = attributes.NetworkAttributes(extract_header=headers.get, remote_addr="99.58.39.5")
        result = network_attrs.standardize()

        # Use X-Forwarded-For as last resort before falling back to remote addr
        self.assertEqual(result["network.client.ip"], "90.32.53.8")

    def test_standardize_without_extra_headers(self):
        network_attrs = attributes.NetworkAttributes(
            extract_header=lambda _: None,
            remote_addr="99.58.39.5",
            bytes_read=10,
            bytes_written=5
        )
        result = network_attrs.standardize()
        self.assertEqual(len(result), 3)
        self.assertEqual(result["network.client.ip"], "99.58.39.5")
        self.assertEqual(result["network.bytes_read"], 10)
        self.assertEqual(result["network.bytes_written"], 5)

    def test_standardize_remote_addr_with_port(self):
        network_attrs = attributes.NetworkAttributes(
            extract_header=lambda _: None,
            remote_addr="99.58.39.5:80"
        )
        result = network_attrs.standardize()
        self.assertEqual(result["network.client.ip"], "99.58.39.5")
        self.assertEqual(result["network.client.port"], "80")

    def test_standardize_remote_addr_ipv6(self):
        network_attrs = attributes.NetworkAttributes(
            extract_header=lambda _: None,
            remote_addr="2001:0db8:85a3:0000:0000:8a2e:0370:7334"
        )
        result = network_attrs.standardize()
        # Should get short form of ipv6 back
        self.assertEqual(result["network.client.ip"], "2001:db8:85a3::8a2e:370:7334")

    def test_standardize_remote_addr_ipv6_with_port(self):
        network_attrs = attributes.NetworkAttributes(
            extract_header=lambda _: None,
            remote_addr="[2001:0db8:85a3:0000:0000:8a2e:0370:7334]:443"
        )
        result = network_attrs.standardize()
        # Should get short form of ipv6 back, and brackets should be removed.
        self.assertEqual(result["network.client.ip"], "2001:db8:85a3::8a2e:370:7334")
        self.assertEqual(result["network.client.port"], "443")


class HttpAttributesTestCase(ClearContext, unittest.TestCase):

    def test_standardize_without_extra_headers(self):
        http_attrs = attributes.HttpAttributes(
            extract_header=lambda _: None,
            url="https://www.example.com/ok?param=fake",
            method="POST",
            status_code=200
        )
        result = http_attrs.standardize()
        self.assertEqual(len(result), 3)
        self.assertEqual(result["http.url"], "https://www.example.com/ok?param=fake")
        self.assertEqual(result["http.method"], "POST")
        self.assertEqual(result["http.status_code"], 200)

    def test_standardize_with_request_id(self):
        headers = {
            "X-Request-Id": "MeFirst",
            "X-Amzn-Trace-Id": "Root=fake"
        }
        http_attrs = attributes.HttpAttributes(
            extract_header=headers.get,
            url="https://www.example.com/ok?param=fake",
            method="POST",
            status_code=200
        )
        result = http_attrs.standardize()
        self.assertEqual(result["http.request_id"], "MeFirst")

        del headers["X-Request-Id"]

        http_attrs = attributes.HttpAttributes(
            extract_header=headers.get,
            url="https://www.example.com/ok?param=fake",
            method="POST",
            status_code=200
        )

        result = http_attrs.standardize()
        self.assertEqual(result["http.request_id"], "Root=fake")
