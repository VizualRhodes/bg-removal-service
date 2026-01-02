"""
U²-Net Model Loader and Background Removal
Uses rembg library for easy U²-Net integration
"""

import io
import logging
from typing import Optional
from PIL import Image
import numpy as np

try:
    from rembg import remove
    REMBG_AVAILABLE = True
except ImportError:
    REMBG_AVAILABLE = False
    logging.warning("rembg library not available. Install with: pip install rembg")

logger = logging.getLogger(__name__)


class BackgroundRemover:
    """
    Background removal using U²-Net model via rembg library
    """
    
    def __init__(self):
        """Initialize the background remover"""
        if not REMBG_AVAILABLE:
            raise RuntimeError(
                "rembg library is not installed. "
                "Install it with: pip install rembg[new]"
            )
        
        # Test model loading on first use
        logger.info("Initializing U²-Net model (via rembg)...")
        try:
            # rembg will download model on first use
            # Test with a small dummy image
            test_image = Image.new('RGB', (100, 100), color='white')
            test_bytes = io.BytesIO()
            test_image.save(test_bytes, format='PNG')
            test_bytes.seek(0)
            
            # This will trigger model download if needed
            _ = remove(test_bytes.getvalue())
            logger.info("U²-Net model ready")
        except Exception as e:
            logger.error(f"Failed to initialize model: {str(e)}")
            raise
    
    def remove_background(self, image_data: bytes) -> bytes:
        """
        Remove background from image
        
        Args:
            image_data: Raw image bytes (JPG or PNG)
        
        Returns:
            PNG bytes with transparent background
        """
        try:
            # Validate image
            image = Image.open(io.BytesIO(image_data))
            
            # Get original format
            original_format = image.format
            
            # Resize if too large (max 2048px on longest side for performance)
            max_size = 2048
            if max(image.size) > max_size:
                ratio = max_size / max(image.size)
                new_size = (int(image.size[0] * ratio), int(image.size[1] * ratio))
                image = image.resize(new_size, Image.Resampling.LANCZOS)
                logger.info(f"Resized image from {image.size} to {new_size}")
            
            # Convert to RGB if needed (rembg expects RGB)
            if image.mode != 'RGB':
                if image.mode == 'RGBA':
                    # Create white background for RGBA images
                    rgb_image = Image.new('RGB', image.size, (255, 255, 255))
                    rgb_image.paste(image, mask=image.split()[3] if image.mode == 'RGBA' else None)
                    image = rgb_image
                else:
                    image = image.convert('RGB')
            
            # Save to bytes for rembg
            input_bytes = io.BytesIO()
            image.save(input_bytes, format='PNG')
            input_bytes.seek(0)
            
            # Run U²-Net inference
            output_bytes = remove(input_bytes.getvalue())
            
            # Ensure output is RGBA PNG
            output_image = Image.open(io.BytesIO(output_bytes))
            
            # Convert to RGBA if not already
            if output_image.mode != 'RGBA':
                output_image = output_image.convert('RGBA')
            
            # Save as PNG with transparency
            result_bytes = io.BytesIO()
            output_image.save(result_bytes, format='PNG')
            result_bytes.seek(0)
            
            return result_bytes.getvalue()
            
        except Exception as e:
            logger.error(f"Error in background removal: {str(e)}")
            raise RuntimeError(f"Failed to remove background: {str(e)}")
    
    def preprocess_image(self, image: Image.Image) -> Image.Image:
        """
        Preprocess image for U²-Net
        
        Args:
            image: PIL Image
        
        Returns:
            Preprocessed PIL Image
        """
        # Resize if needed
        max_size = 2048
        if max(image.size) > max_size:
            ratio = max_size / max(image.size)
            new_size = (int(image.size[0] * ratio), int(image.size[1] * ratio))
            image = image.resize(new_size, Image.Resampling.LANCZOS)
        
        # Convert to RGB
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        return image

