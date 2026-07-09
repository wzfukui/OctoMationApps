# coding: utf-8
from hillstonenet_ti import detail_url, detail_ip, detail_domain,detail_file
import os
import unittest
import time
import random


HILLSTONENET_TI_API_KEY = os.getenv("HILLSTONENET_TI_API_KEY")
HILLSTONENET_TI_API_DOMAIN = os.getenv("HILLSTONENET_TI_API_DOMAIN", "ti.hillstonenet.com.cn")


class TestHillstonenetTi(unittest.TestCase):
    def __init__(self, methodName: str = "runTest") -> None:
        super().__init__(methodName)
        self.assets = {
            "api_key": HILLSTONENET_TI_API_KEY or "",
            "api_domain": HILLSTONENET_TI_API_DOMAIN
        }
        self.params = {
            "ip": "184.32.167.72",
            "domain": "github.com",
            "url": "https://github.com/",
            "file_hash": "02cfbb7326fd467f87a810921cfebe9e"
        }

    @unittest.skipUnless(HILLSTONENET_TI_API_KEY, "requires HILLSTONENET_TI_API_KEY")
    def test_detail_url(self):
        time.sleep(random.randint(10, 60))
        ret = detail_url(self.params, self.assets, None)
        self.assertEqual(ret['data']['err_code'], 0)

    @unittest.skipUnless(HILLSTONENET_TI_API_KEY, "requires HILLSTONENET_TI_API_KEY")
    def test_detail_ip(self):
        time.sleep(random.randint(10, 60))
        ret = detail_ip(self.params, self.assets, None)
        self.assertEqual(ret['data']['err_code'], 0)

    @unittest.skipUnless(HILLSTONENET_TI_API_KEY, "requires HILLSTONENET_TI_API_KEY")
    def test_detail_domain(self):
        time.sleep(random.randint(10, 60))
        ret = detail_domain(self.params, self.assets, None)
        self.assertEqual(ret['data']['err_code'], 0)

    @unittest.skipUnless(HILLSTONENET_TI_API_KEY, "requires HILLSTONENET_TI_API_KEY")
    def test_detail_file(self):
        time.sleep(random.randint(10, 60))
        ret = detail_file(self.params, self.assets, None)
        self.assertEqual(ret['data']['err_code'], 0)


if __name__ == '__main__':
    print("\n防止并发导致接口调用触发频次限制，随机延时1-10秒")
    unittest.main()
