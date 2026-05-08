import json
import os
import wpf
from System.Windows import Window, Application
from System.Windows.Controls import Canvas, TextBlock
from System.Windows.Shapes import Line, Ellipse
from System.Windows.Media import Brushes, SolidColorBrush, Color

class PreviewWindow(Window):
    def __init__(self, xaml_file, preview_json_path):
        wpf.LoadComponent(self, xaml_file)
        self.preview_data = {}
        self.result = False # True if User clicks OK
        
        if os.path.exists(preview_json_path):
            with open(preview_json_path, 'r') as f:
                self.preview_data = json.load(f)
                
        self.draw_preview()
        
    def draw_preview(self):
        canvas = self.FindName("PreviewCanvas")
        if not canvas: return
        
        # Draw Lines
        for l in self.preview_data.get("lines", []):
            line = Line()
            line.X1 = l["x1"]
            line.Y1 = l["y1"]
            line.X2 = l["x2"]
            line.Y2 = l["y2"]
            line.Stroke = Brushes.White
            line.StrokeThickness = 1.0
            canvas.Children.Add(line)
            
        # Draw Text/Symbols (Simplified)
        for t in self.preview_data.get("text", []):
            tb = TextBlock()
            tb.Text = t["text"]
            tb.Foreground = Brushes.Yellow
            tb.FontSize = t.get("h", 5)
            # Position (In WPF Canvas Top-Left is 0,0, but we flipped Y in XAML)
            # Actually, TextBlock might render upside down if we flipped the Canvas!
            # We might need to unflip the text element itself.
            
            Canvas.SetLeft(tb, t["x"])
            Canvas.SetTop(tb, t["y"])
            
            # Correction for Flip: scale text back
            # tb.RenderTransformOrigin = Point(0.5, 0.5)
            # tb.RenderTransform = ScaleTransform(1, -1) 
            # Doing this correctly in code is tricky without complex transform logic.
            # Simplified: Just draw circles for now for nodes
            
            pixel = Ellipse()
            pixel.Width = 4
            pixel.Height = 4
            pixel.Fill = Brushes.Cyan
            Canvas.SetLeft(pixel, t["x"] - 2)
            Canvas.SetTop(pixel, t["y"] - 2)
            canvas.Children.Add(pixel)

    def BtnOK_Click(self, sender, e):
        self.result = True
        self.Close()
        
    def BtnCancel_Click(self, sender, e):
        self.result = False
        self.Close()
