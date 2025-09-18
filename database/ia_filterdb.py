import logging
import re
import base64
from struct import pack
from pymongo import MongoClient, TEXT
from pymongo.errors import DuplicateKeyError, OperationFailure
from hydrogram.file_id import FileId
from info import USE_CAPTION_FILTER, FILES_DATABASE_URL, SECOND_FILES_DATABASE_URL, DATABASE_NAME, COLLECTION_NAME, MAX_BTN

logger = logging.getLogger(__name__)

# -------------------------
# Initialize primary database
# -------------------------
client = MongoClient(FILES_DATABASE_URL)
db = client[DATABASE_NAME]
collection = db[COLLECTION_NAME]

try:
    collection.create_index([("file_name", TEXT)])
except OperationFailure as e:
    if 'quota' in str(e).lower():
        if not SECOND_FILES_DATABASE_URL:
            logger.error('Your FILES_DATABASE_URL is full, add SECOND_FILES_DATABASE_URL')
        else:
            logger.info('FILES_DATABASE_URL is full, now using SECOND_FILES_DATABASE_URL')
    else:
        logger.exception(e)

# -------------------------
# Initialize secondary database (optional)
# -------------------------
second_collection = None
if SECOND_FILES_DATABASE_URL:
    second_client = MongoClient(SECOND_FILES_DATABASE_URL)
    second_db = second_client[DATABASE_NAME]
    second_collection = second_db[COLLECTION_NAME]
    second_collection.create_index([("file_name", TEXT)])


# -------------------------
# Helper functions
# -------------------------
def db_count_documents():
    return collection.count_documents({})

def second_db_count_documents():
    return second_collection.count_documents({}) if second_collection else 0

def encode_file_id(s: bytes) -> str:
    r = b""
    n = 0
    for i in s + bytes([22]) + bytes([4]):
        if i == 0:
            n += 1
        else:
            if n:
                r += b"\x00" + bytes([n])
                n = 0
            r += bytes([i])
    return base64.urlsafe_b64encode(r).decode().rstrip("=")

def unpack_new_file_id(new_file_id):
    decoded = FileId.decode(new_file_id)
    file_id = encode_file_id(
        pack(
            "<iiqq",
            int(decoded.file_type),
            decoded.dc_id,
            decoded.media_id,
            decoded.access_hash
        )
    )
    return file_id

# -------------------------
# Save a media file in DB
# -------------------------
async def save_file(media):
    file_id = unpack_new_file_id(media.file_id)
    file_name = re.sub(r"@\w+|(_|\-|\.|\+)", " ", str(media.file_name))
    file_caption = re.sub(r"@\w+|(_|\-|\.|\+)", " ", str(media.caption))

    document = {
        '_id': file_id,
        'file_name': file_name,
        'file_size': media.file_size,
        'caption': file_caption
    }

    try:
        collection.insert_one(document)
        logger.info(f'Saved - {file_name}')
        return 'suc'
    except DuplicateKeyError:
        logger.warning(f'Already Saved - {file_name}')
        return 'dup'
    except OperationFailure:
        if second_collection:
            try:
                second_collection.insert_one(document)
                logger.info(f'Saved to 2nd DB - {file_name}')
                return 'suc'
            except DuplicateKeyError:
                logger.warning(f'Already Saved in 2nd DB - {file_name}')
                return 'dup'
        else:
            logger.error('FILES_DATABASE_URL is full, add SECOND_FILES_DATABASE_URL')
            return 'err'

# -------------------------
# Search files
# -------------------------
async def get_search_results(query, max_results=MAX_BTN, offset=0, lang=None):
    query = str(query).strip()
    if not query:
        raw_pattern = '.'
    elif ' ' not in query:
        raw_pattern = r'(\b|[\.\+\-_])' + query + r'(\b|[\.\+\-_])'
    else:
        raw_pattern = query.replace(' ', r'.*[\s\.\+\-_]')

    try:
        regex = re.compile(raw_pattern, flags=re.IGNORECASE)
    except:
        regex = query

    filter_criteria = {'$or': [{'file_name': regex}, {'caption': regex}]} if USE_CAPTION_FILTER else {'file_name': regex}

    results = list(collection.find(filter_criteria))
    if second_collection:
        results.extend(list(second_collection.find(filter_criteria)))

    if lang:
        lang_files = [f for f in results if lang in f['file_name'].lower()]
        files = lang_files[offset:][:max_results]
        total_results = len(lang_files)
        next_offset = offset + max_results if offset + max_results < total_results else ''
        return files, next_offset, total_results

    total_results = len(results)
    files = results[offset:][:max_results]
    next_offset = offset + max_results if offset + max_results < total_results else ''
    return files, next_offset, total_results

# -------------------------
# Delete files matching a query
# -------------------------
async def delete_files(query):
    query = query.strip()
    if not query:
        raw_pattern = '.'
    elif ' ' not in query:
        raw_pattern = r'(\b|[\.\+\-_])' + query + r'(\b|[\.\+\-_])'
    else:
        raw_pattern = query.replace(' ', r'.*[\s\.\+\-_]')

    try:
        regex = re.compile(raw_pattern, flags=re.IGNORECASE)
    except:
        regex = query

    filter_criteria = {'file_name': regex}

    result1 = collection.delete_many(filter_criteria)
    result2 = second_collection.delete_many(filter_criteria) if second_collection else None

    total_deleted = result1.deleted_count
    if result2:
        total_deleted += result2.deleted_count

    return total_deleted

# -------------------------
# Get details of a file by ID
# -------------------------
async def get_file_details(file_id):
    details = collection.find_one({'_id': file_id})
    if not details and second_collection:
        details = second_collection.find_one({'_id': file_id})
    return details