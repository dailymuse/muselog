import unittest

from muselog import attributes, util

from .support import ClearContext


class UtilTestCase(ClearContext, unittest.TestCase):

    def test_log_request(self):
        network_attrs = attributes.NetworkAttributes(
            extract_header=lambda _: None,
            remote_addr="99.58.39.5",
            bytes_read=10,
            bytes_written=5
        )
        http_attrs = attributes.HttpAttributes(
            extract_header={"User-Agent": "Fake", "Referer": "Some Asshole"}.get,
            url="https://www.example.com/ok?param=fake",
            method="GET",
            status_code=301
        )

        with self.assertLogs("muselog.util") as cm:
            util.log_request(
                path="/ok",
                duration_secs=2,
                network_attrs=network_attrs,
                http_attrs=http_attrs,
                user_id=10
            )

            # Should output a single log record
            self.assertEqual(len(cm.records), 1)

            # That record should have our extra attributes where available
            record = cm.records[0].__dict__
            self.assertEqual(record["duration"], 2000000000)
            self.assertEqual(record["network.bytes_read"], 10)
            self.assertEqual(record["network.bytes_written"], 5)
            self.assertEqual(record["http.url"], "https://www.example.com/ok?param=fake")
            self.assertEqual(record["http.method"], "GET")
            self.assertEqual(record["http.status_code"], 301)
            self.assertEqual(record["usr.id"], 10)

            # Request summary should include basic information -- not going to care
            # about the format, so we just check for containment
            output = cm.output[0]
            self.assertIn("2000.00ms", output)
            self.assertIn("301", output)
            self.assertIn("/ok", output)
            self.assertIn("99.58.39.5", output)
            self.assertIn("GET", output)
