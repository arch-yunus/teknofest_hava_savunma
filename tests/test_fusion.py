import unittest
from src.network_manager import NetworkManager

class TestTrackFusion(unittest.TestCase):
    def setUp(self):
        self.nm = NetworkManager()

    def test_fusion_no_duplicates(self):
        local_tracks = [{"id": "LOCAL-1", "x": 10, "y": 10, "z": 5}]
        remote_tracks = [
            {"id": "LOCAL-1", "x": 10, "y": 10, "z": 5}, # Duplicate
            {"id": "REMOTE-1", "x": 50, "y": 50, "z": 10} # New
        ]
        
        self.nm.receive_remote_data("BATARYA-2", remote_tracks)
        fused = self.nm.get_recognized_air_picture(local_tracks)
        
        # Test 1: Toplam 2 iz olmalı (LOCAL-1 ve REMOTE-1)
        self.assertEqual(len(fused), 2)
        
        # Test 2: REMOTE-1 'is_remote' olarak işaretlenmeli
        remote_track = next((t for t in fused if t["id"] == "REMOTE-1"), None)
        self.assertTrue(remote_track.get("is_remote"))
        self.assertEqual(remote_track.get("source_battery"), "BATARYA-2")

if __name__ == '__main__':
    unittest.main()
