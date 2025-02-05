import unittest
import pandrawer

class TestPangenomeGFAJson(unittest.TestCase):
    def test_extract_coordinates(self):
        # Example: Test extracting coordinates from a sample image
        image_path = "test_image.png"  # You should provide a valid test image
        points = pandrawer.extract_coordinates(image_path)
        self.assertIsInstance(points, list)
        self.assertTrue(all(isinstance(pt, list) and len(pt) == 2 for pt in points))
    
    def test_generate_gfa(self):
        points = [[0, 0], [10, 10], [20, 20]]
        gfa = pandrawer.generate_gfa(points)
        self.assertTrue(any(line.startswith("H") for line in gfa))  # Ensure header exists
        self.assertTrue(any(line.startswith("S") for line in gfa))  # Ensure nodes exist
    
    def test_generate_json_layout(self):
        points = [[0, 0], [10, 10], [20, 20]]
        gfa = pandrawer.generate_gfa(points)
        json_layout = pandrawer.generate_json_layout(points, gfa)
        self.assertIn("1+", json_layout)  # Check if node exists in layout
    
if __name__ == "__main__":
    unittest.main()