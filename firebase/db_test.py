import datetime
from firebase_admin import firestore
import firebase_admin
from firebase_admin import credentials


def main():
    # ===================== Firebase =====================================
    # このPythonファイルと同じ階層に認証ファイルを配置して、ファイル名を格納
    JSON_PATH = 'authentication.json'   # Notionに貼った

    # Firebase初期化
    cred = credentials.Certificate(JSON_PATH)
    firebase_admin.initialize_app(cred)
    db = firestore.client()
    # ====================================================================

    dt_now = datetime.datetime.now()

    try:
        # Firestoreのコレクションにアクセス
        doc_ref = db.collection('test')
        # Firestoreにドキュメントidを指定しないで１つずつ保存
        doc_ref.add({
            'title': "test",
            'date': str(dt_now),
        })
        
        #　読み込み
        docs = doc_ref.stream()
        for doc in docs:
            print(f"{doc.id} => {doc.to_dict()}")
    except Exception as e:
        print(e)

    print('done')


if __name__ == '__main__':
    main()