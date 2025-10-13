"""
Google Cloud Configuration utilities for AgentMesh
Handles authentication, project settings, and service initialization
"""
import os
from typing import Optional
from google.cloud import aiplatform
from google.oauth2 import service_account
import logging

logger = logging.getLogger(__name__)

class GoogleCloudConfig:
    """
    Configuration class for Google Cloud services
    """
    
    def __init__(self, project_id: Optional[str] = None, location: str = "us-central1"):
        self.project_id = project_id or os.getenv("GOOGLE_CLOUD_PROJECT")
        self.location = location or os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
        self.credentials = None
        
        # Validate required configuration
        if not self.project_id:
            raise ValueError("Google Cloud project ID must be provided either as parameter or via GOOGLE_CLOUD_PROJECT environment variable")
        
        # Initialize credentials
        self._initialize_credentials()
        
        # Initialize Vertex AI
        self._initialize_vertex_ai()
    
    def _initialize_credentials(self):
        """
        Initialize Google Cloud credentials from service account key or default credentials
        """
        try:
            # Check for service account key file
            service_account_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
            if service_account_path and os.path.exists(service_account_path):
                self.credentials = service_account.Credentials.from_service_account_file(
                    service_account_path
                )
                logger.info(f"Loaded credentials from service account file: {service_account_path}")
            else:
                # Use default credentials (for use in GCP environments)
                logger.info("Using default Google Cloud credentials")
        except Exception as e:
            logger.warning(f"Could not initialize credentials: {e}")
            logger.info("Ensure proper authentication is set up (service account key or default credentials)")
    
    def _initialize_vertex_ai(self):
        """
        Initialize Vertex AI with project settings
        """
        try:
            aiplatform.init(
                project=self.project_id,
                location=self.location,
                credentials=self.credentials
            )
            logger.info(f"Vertex AI initialized for project: {self.project_id}, location: {self.location}")
        except Exception as e:
            logger.error(f"Error initializing Vertex AI: {e}")
            raise
    
    def get_project_id(self) -> str:
        """
        Get the configured project ID
        """
        return self.project_id
    
    def get_location(self) -> str:
        """
        Get the configured location
        """
        return self.location
    
    def get_credentials(self):
        """
        Get the configured credentials
        """
        return self.credentials

# Global configuration instance
_gcp_config: Optional[GoogleCloudConfig] = None

def get_gcp_config() -> GoogleCloudConfig:
    """
    Get the global Google Cloud configuration instance
    """
    global _gcp_config
    if _gcp_config is None:
        _gcp_config = GoogleCloudConfig()
    return _gcp_config

def configure_gcp(project_id: Optional[str] = None, location: str = "us-central1") -> GoogleCloudConfig:
    """
    Configure Google Cloud settings globally
    """
    global _gcp_config
    _gcp_config = GoogleCloudConfig(project_id=project_id, location=location)
    return _gcp_config