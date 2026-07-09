#coding: utf-8
import os
import unittest
from scamalytics import get_ip_fraud_risk_info, health_check


SCAMALYTICS_API_KEY = os.getenv("SCAMALYTICS_API_KEY")
SCAMALYTICS_API_USER = os.getenv("SCAMALYTICS_API_USER", "")


class TestScamalytics(unittest.TestCase):
    def __init__(self, methodName: str = "runTest") -> None:
        super().__init__(methodName)
        self.assets = {
            "api_user": SCAMALYTICS_API_USER,
            "api_key": SCAMALYTICS_API_KEY or ""
        }

    @unittest.skipUnless(SCAMALYTICS_API_KEY, "requires SCAMALYTICS_API_KEY")
    def test_lan_ip(self):
        params = {
            "ip": "192.168.127.12"
        }
        risk_info = get_ip_fraud_risk_info(params, self.assets, None)
        self.assertEqual(risk_info['data']['isp_name'], 'Private network')

    @unittest.skipUnless(SCAMALYTICS_API_KEY, "requires SCAMALYTICS_API_KEY")
    def test_cn_home_ip(self):
        params = {
            "ip": "222.67.207.4"
        }
        risk_info = get_ip_fraud_risk_info(params, self.assets, None)
        self.assertEqual(risk_info['data']['ip_state_name'], 'Shanghai')
    
    @unittest.skipUnless(SCAMALYTICS_API_KEY, "requires SCAMALYTICS_API_KEY")
    def test_hk_server_ip(self):
        params = {
            "ip": "119.28.82.185"
        }
        risk_info = get_ip_fraud_risk_info(params, self.assets, None)
        self.assertTrue(risk_info['data']['server'])

    @unittest.skipUnless(SCAMALYTICS_API_KEY, "requires SCAMALYTICS_API_KEY")
    def test_proxy_ip(self):
        params = {
            "ip": "216.58.194.174"
        }
        risk_info = get_ip_fraud_risk_info(params, self.assets, None)
        self.assertGreater(risk_info['data']['score'], 0)

    # @unittest.skip("skip")
    def test_get_ip_fraud_risk_without_api_key(self):
        assets = {}
        params = {
            "ip": "216.58.194.174"
        }
        risk_info = get_ip_fraud_risk_info(params, assets, None)
        self.assertEqual(risk_info['data']['err_code'], 0)

    # @unittest.skip("skip")
    def test_health_check(self):
        params= {}
        assets = {}
        risk_info = health_check(params, assets, None)
        self.assertEqual(risk_info['summary']['statusCode'], 200)
        risk_info = health_check(params, self.assets, None)
        self.assertEqual(risk_info['summary']['statusCode'], 200)

if __name__ == '__main__':
    unittest.main()
