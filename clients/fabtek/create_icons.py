import struct
import zlib
import os

def write_png(filename, color_logic):
    width = 32
    height = 32
    
    # PNG Signature
    png_sig = b'\x89PNG\r\n\x1a\n'
    
    # IHDR Chunk
    # Width, Height, BitDepth(8), ColorType(6=RGBA), Compress(0), Filter(0), Interlace(0)
    ihdr_data = struct.pack('!IIBBBBB', width, height, 8, 6, 0, 0, 0)
    ihdr_crc = zlib.crc32(b'IHDR' + ihdr_data)
    ihdr = struct.pack('!I', len(ihdr_data)) + b'IHDR' + ihdr_data + struct.pack('!I', ihdr_crc)
    
    # IDAT Chunk (Raw Pixel Data)
    raw_data = b''
    for y in range(height):
        # Scanline filter 0 (None) per row
        row = b'\x00' 
        for x in range(width):
            r, g, b, a = color_logic(x, y)
            row += struct.pack('BBBB', r, g, b, a)
        raw_data += row
            
    compressed = zlib.compress(raw_data)
    idat_crc = zlib.crc32(b'IDAT' + compressed)
    # Length, Type, Data, CRC
    idat = struct.pack('!I', len(compressed)) + b'IDAT' + compressed + struct.pack('!I', idat_crc)
    
    # IEND Chunk
    iend_crc = zlib.crc32(b'IEND')
    iend_len = struct.pack('!I', 0)
    iend = iend_len + b'IEND' + struct.pack('!I', iend_crc)
    
    with open(filename, 'wb') as f:
        f.write(png_sig + ihdr + idat + iend)
    print("Generated: " + filename)

def logic_generate(x, y):
    # Green Play Triangle
    # Center at 16,16
    # Triangle pointing right
    # (8, 6), (8, 26), (26, 16)
    in_tri = False
    if x >= 8 and x <= 24:
        # Check slope
        # y_top given x: lerp(8->16, 26->16) 
        # Actually easier: slope is (10/16) approx 0.6
        half_height = (x-8) * 0.6 + 2 # small width at start
        if y >= 16 - half_height and y <= 16 + half_height:
             return 0, 200, 0, 255
    return 255, 255, 255, 0 # Transparent

def logic_skey(x, y):
    # Blue Lines / List
    if y % 8 in [3, 4, 5] and x > 6 and x < 26:
        return 0, 100, 255, 255
    # Bullet points
    if y % 8 in [3, 4, 5] and x > 2 and x < 5:
        return 0, 100, 255, 255
    return 255, 255, 255, 0

def logic_setup(x, y):
    # Orange Page with Gear
    if x > 6 and x < 26 and y > 4 and y < 28:
        if x in [6, 26] or y in [5, 27] or y == 10:
             return 0, 0, 0, 255
        return 255, 200, 100, 255
    return 255, 255, 255, 0

def logic_options(x, y):
    # Grey Gear Circle
    dist = ((x-16)**2 + (y-16)**2)**0.5
    if dist < 12 and dist > 4:
         return 100, 100, 100, 255
    return 255, 255, 255, 0

if __name__ == "__main__":
    out_dir = "clients/fabtek/resources/icons"
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)
        
    write_png(os.path.join(out_dir, "generate.png"), logic_generate)
    write_png(os.path.join(out_dir, "skey_def.png"), logic_skey)
    write_png(os.path.join(out_dir, "setup.png"), logic_setup)
    write_png(os.path.join(out_dir, "options.png"), logic_options)
