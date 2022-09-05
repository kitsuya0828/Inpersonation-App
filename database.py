import firebase_admin
from firebase_admin import credentials, firestore, storage
import datetime
import uuid

class DB:
    def __init__(self, cert: dict):
        cred = credentials.Certificate(cert)    # https://github.com/firebase/firebase-admin-python/blob/master/firebase_admin/credentials.py#L85
        firebase_admin.initialize_app(cred, {'storageBucket': 'mimic-dda0d.appspot.com'})
        self.db = firestore.client()
        self.bucket = storage.bucket()

    def firestore_add(self, collection_name="test", values={}):
        doc_ref = self.db.collection(collection_name)
        doc_ref.add({
            'title': str(uuid.uuid4()),
            'date': str(datetime.datetime.now()),
        })
        return "success"
    
    def firestore_stream(self, collection_name="test"):
        doc_ref = self.db.collection(collection_name)
        docs = doc_ref.stream()
        for doc in docs:
            print(f"{doc.id} => {doc.to_dict()}")
        return docs
    
    def bucket_upload(self, file_path, blob_path):
        try:
            blob = self.bucket.blob(blob_path)
            blob.upload_from_filename(file_path)
            return True
        except Exception as e:
            print(e)
            return False
    
    def bucket_download(self, blob_path, file_path):
        try:
            blob = self.bucket.get_blob(blob_path)
            blob.download_to_filename(file_path)
            return True
        except Exception as e:
            print(e)
            return False
