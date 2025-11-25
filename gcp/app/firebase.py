import firebase_admin
from firebase_admin import credentials, firestore, storage
from typing import Dict, Any, Optional, List
import logging
from datetime import datetime

from .config import settings

logger = logging.getLogger(__name__)

class FirebaseClient:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            try:
                cred = credentials.Certificate(settings.FIREBASE_CREDENTIALS_PATH)
                firebase_admin.initialize_app(cred, {
                    'storageBucket': 'atomic-lens-471613-m4.appspot.com'
                })
                self.db = firestore.client()
                self.bucket = storage.bucket()
                self._initialized = True
                logger.info("Firebase initialized successfully")
            except Exception as e:
                logger.error(f"Firebase initialization failed: {e}")
                raise
    
    # ============= Firestore Operations =============
    
    def save_document(self, collection: str, doc_id: str, data: Dict[str, Any]) -> bool:
        """Save document to Firestore"""
        try:
            data['updated_at'] = datetime.now()
            self.db.collection(collection).document(doc_id).set(data, merge=True)
            logger.info(f"Document saved: {collection}/{doc_id}")
            return True
        except Exception as e:
            logger.error(f"Error saving document: {e}")
            return False
    
    def get_document(self, collection: str, doc_id: str) -> Optional[Dict[str, Any]]:
        """Get document from Firestore"""
        try:
            doc = self.db.collection(collection).document(doc_id).get()
            return doc.to_dict() if doc.exists else None
        except Exception as e:
            logger.error(f"Error getting document: {e}")
            return None
    
    def query_documents(self, collection: str, filters: Dict[str, Any], limit: int = 100) -> List[Dict[str, Any]]:
        """Query documents with filters"""
        try:
            query = self.db.collection(collection)
            for field, value in filters.items():
                query = query.where(field, "==", value)
            docs = query.limit(limit).stream()
            return [doc.to_dict() for doc in docs]
        except Exception as e:
            logger.error(f"Error querying documents: {e}")
            return []
    
    def delete_document(self, collection: str, doc_id: str) -> bool:
        """Delete document from Firestore"""
        try:
            self.db.collection(collection).document(doc_id).delete()
            logger.info(f"Document deleted: {collection}/{doc_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting document: {e}")
            return False
    
    # ============= Storage Operations =============
    
    def upload_file(self, file_path: str, destination: str) -> Optional[str]:
        """Upload file to Firebase Storage"""
        try:
            blob = self.bucket.blob(destination)
            blob.upload_from_filename(file_path)
            blob.make_public()
            logger.info(f"File uploaded: {destination}")
            return blob.public_url
        except Exception as e:
            logger.error(f"Error uploading file: {e}")
            return None
    
    def download_file(self, source: str, destination: str) -> bool:
        """Download file from Firebase Storage"""
        try:
            blob = self.bucket.blob(source)
            blob.download_to_filename(destination)
            logger.info(f"File downloaded: {source}")
            return True
        except Exception as e:
            logger.error(f"Error downloading file: {e}")
            return False
    
    def delete_file(self, file_path: str) -> bool:
        """Delete file from Firebase Storage"""
        try:
            blob = self.bucket.blob(file_path)
            blob.delete()
            logger.info(f"File deleted: {file_path}")
            return True
        except Exception as e:
            logger.error(f"Error deleting file: {e}")
            return False

# Singleton instance
firebase_client = FirebaseClient()