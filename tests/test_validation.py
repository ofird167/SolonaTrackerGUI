import unittest
import re

class TestValidation(unittest.TestCase):
    def test_solana_address_regex(self):
        # Valid Solana addresses
        valid_addresses = [
            "7xKXozay1zXiGS62k5fqajsS1yY164u35PfZF91x186b",
            "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
            "So11111111111111111111111111111111111111112"
        ]
        # Invalid Solana addresses
        invalid_addresses = [
            "not-an-address",
            "7xKXozay1zXiGS62k5fqajsS1yY164u35PfZF91x186b-extra",
            "O0I1" # Invalid base58 characters (O, 0, I, l)
        ]
        
        regex = r"^[1-9A-HJ-NP-Za-km-z]{32,44}$"
        for addr in valid_addresses:
            self.assertTrue(re.match(regex, addr) is not None, f"Failed on valid address: {addr}")
        for addr in invalid_addresses:
            self.assertFalse(re.match(regex, addr) is not None, f"Failed on invalid address: {addr}")

if __name__ == "__main__":
    unittest.main()
