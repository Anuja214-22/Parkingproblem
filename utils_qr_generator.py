import qrcode
from io import BytesIO
import base64

def generate_qr_code(data):
    """
    Generate QR code from given data
    
    Args:
        data: String data to encode in QR code
    
    Returns:
        str: Base64 encoded QR code image
    """
    try:
        # Create QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        
        qr.add_data(data)
        qr.make(fit=True)
        
        # Create image
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to bytes
        buffered = BytesIO()
        img.save(buffered, format="PNG")
        buffered.seek(0)
        
        # Encode to base64
        img_str = base64.b64encode(buffered.getvalue()).decode()
        
        return f"data:image/png;base64,{img_str}"
    
    except Exception as e:
        print(f"QR Code generation error: {e}")
        return None