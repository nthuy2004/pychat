from flask import request, jsonify
import oss2
import os
from storage import bucket, DIR_PREFIX, get_url

from config import Config

from werkzeug.utils import secure_filename

DISALLOW_EXTS = {'exe', 'cmd', 'bat', 'com', 'lnk', 'vbs', 'msi', 'vb', 'ws', 'scr'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() not in DISALLOW_EXTS

def remove(file_id):
    file_url = f"{DIR_PREFIX}/{file_id}"
    result = bucket.delete_object(file_url)
    return jsonify({"message": "opps..."}), result.status

def upload():
    if 'files' not in request.files:
        return jsonify({'error': 'Empty request'}), 400

    files = request.files.getlist('files')

    output = []

    for file in files:
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)

            unique_filename = f"{os.urandom(8).hex()}_{filename}"
            
            upload_file_namee = f"{DIR_PREFIX}/{unique_filename}"

            try:
                result = bucket.put_object(upload_file_namee, file)
                
                if result.status == 200:
                    file_url = get_url(unique_filename)
                    mimetype = file.content_type
                    output.append({
                        "upload_filename": unique_filename,
                        "original_filename": file.filename,
                        "upload_url": file_url,
                        "mimetype": mimetype
                    })

                    # output.append({
                    #     "upload_filename": "video/fmimg/520ba14d4668d4ca_logo.jpg",
                    #     "original_filename": "logo.jpg",
                    #     "upload_url": "https://minhtu.oss-ap-southeast-1.aliyuncs.com/video/fmimg/520ba14d4668d4ca_logo.jpg",
                    #     "mimetype": "image/jpeg"
                    # })

            except oss2.exceptions.OssError as e:
                return jsonify({'error_code': 'error', 'message': f"cannot upload {filename}: {str(e)}"}), 500

    return jsonify(output)