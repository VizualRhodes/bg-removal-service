"""
FastAPI Application for U²-Net Background Removal
Production-grade AI microservice
"""

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import logging
from typing import Optional
import time

from model_loader import BackgroundRemover

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="U²-Net Background Removal API",
    description="Production-grade background removal service using U²-Net",
    version="1.0.0"
)

# CORS middleware (configure for production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure specific origins in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global model instance (loaded at startup)
bg_remover: Optional[BackgroundRemover] = None


@app.on_event("startup")
async def startup_event():
    """Load U²-Net model at application startup"""
    global bg_remover
    try:
        logger.info("Loading U²-Net model...")
        bg_remover = BackgroundRemover()
        logger.info("U²-Net model loaded successfully")
    except Exception as e:
        logger.error(f"Failed to load U²-Net model: {str(e)}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    global bg_remover
    bg_remover = None
    logger.info("Application shutdown complete")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "model_loaded": bg_remover is not None,
        "service": "u2net-background-removal"
    }


@app.post("/remove-bg")
async def remove_background(file: UploadFile = File(...)):
    """
    Remove background from uploaded image using U²-Net
    
    Args:
        file: Image file (JPG or PNG)
    
    Returns:
        PNG image with transparent background
    """
    if bg_remover is None:
        raise HTTPException(
            status_code=503,
            detail="Background removal service is not available. Model not loaded."
        )
    
    # Validate file type
    if file.content_type not in ["image/jpeg", "image/png", "image/jpg"]:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Only JPG and PNG are supported. Got: {file.content_type}"
        )
    
    try:
        # Read uploaded file
        image_data = await file.read()
        
        # Validate file size (10MB max)
        max_size = 10 * 1024 * 1024  # 10MB
        if len(image_data) > max_size:
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Maximum size is 10MB. Got: {len(image_data)} bytes"
            )
        
        logger.info(f"Processing image: {file.filename}, size: {len(image_data)} bytes")
        start_time = time.time()
        
        # Process image
        result_png = bg_remover.remove_background(image_data)
        
        processing_time = time.time() - start_time
        logger.info(f"Background removal completed in {processing_time:.2f} seconds")
        
        # Return PNG with proper headers
        return Response(
            content=result_png,
            media_type="image/png",
            headers={
                "Content-Disposition": 'attachment; filename="bgremoved.png"',
                "X-Processing-Time": f"{processing_time:.2f}"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing image: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process image: {str(e)}"
        )


if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )

