import unittest
from app.common import sign_payload, verify_signature

class SecurityTests(unittest.TestCase):
    def test_valid_signature(self):
        payload = {"node_id": "controller1", "result": "ACCEPTED", "operation_id": "op-123"}
        self.assertTrue(verify_signature("controller1", payload,
                                         sign_payload("controller1", payload)))

    def test_modified_payload_is_rejected(self):
        payload = {"node_id": "controller1", "result": "ACCEPTED", "operation_id": "op-123"}
        signature = sign_payload("controller1", payload)
        self.assertFalse(verify_signature("controller1",
                          {**payload, "result": "REJECTED"}, signature))

    def test_replica_keys_are_distinct(self):
        payload = {"result": "ACCEPTED"}
        self.assertFalse(verify_signature("controller2", payload,
                                          sign_payload("controller1", payload)))

if __name__ == "__main__":
    unittest.main()
