import unittest
from src.detection.model import DetectionModel

class TestDetectionModel(unittest.TestCase):
    def setUp(self):
        self.model = DetectionModel()

    def test_nominal_features_prediction(self):
        nominal_features = {
            'bytes_sent': 500,
            'bytes_received': 1200,
            'connections': 2,
            'failed_logins': 0,
            'dns_requests': 1,
            'cpu_usage': 15.0,
            'mem_usage': 30.0
        }
        is_threat, score = self.model.predict(nominal_features)
        self.assertFalse(is_threat)
        self.assertLess(score, 0.45)

    def test_brute_force_attack_prediction(self):
        attack_features = {
            'bytes_sent': 500000,
            'bytes_received': 3000,
            'connections': 12,
            'failed_logins': 18,
            'dns_requests': 0,
            'cpu_usage': 92.0,
            'mem_usage': 80.0
        }
        is_threat, score = self.model.predict(attack_features)
        self.assertTrue(is_threat)
        self.assertGreaterEqual(score, 0.70)

    def test_ransomware_exhaustion_heuristic(self):
        ransomware_features = {
            'bytes_sent': 1000,
            'bytes_received': 500,
            'connections': 2,
            'failed_logins': 0,
            'dns_requests': 2,
            'cpu_usage': 99.0,
            'mem_usage': 95.0
        }
        is_threat, score = self.model.predict(ransomware_features)
        self.assertTrue(is_threat)
        self.assertGreaterEqual(score, 0.80)

if __name__ == '__main__':
    unittest.main()
