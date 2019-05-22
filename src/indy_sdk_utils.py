""" Wrappers around Indy-SDK functions to overcome shortcomings in the SDK.
"""
import json
from messages.message import Message
from indy import wallet, did, non_secrets, error, crypto

async def get_did_metadata(wallet_handle, subject_did):
    meta = {}
    try:
        meta = await did.get_did_metadata(wallet_handle, subject_did)
    except error.IndyError as e:
        if e.error_code is error.ErrorCode.WalletItemNotFound:
            pass
        else:
            raise e

    return json.loads(meta) if meta else {}

async def set_did_metadata(wallet_handle, subject_did, metadata):
    await did.set_did_metadata(wallet_handle, subject_did, json.dumps(metadata))

async def unpack(wallet_handle, message_bytes):
    try:
        unpacked = json.loads(
            await crypto.unpack_message(
                wallet_handle,
                message_bytes
            )
        )

        from_key = None
        from_did = None
        if 'sender_verkey' in unpacked:
            from_key = unpacked['sender_verkey']
            from_did = await did_for_key(wallet_handle, unpacked['sender_verkey'])

        to_key = unpacked['recipient_verkey']
        to_did = await did_for_key(wallet_handle, unpacked['recipient_verkey'])

        msg = Message.deserialize(unpacked['message'])

        msg.context = {
            'from_did': from_did,
            'to_did': to_did,
            'from_key': from_key,
            'to_key': to_key
        }
        return msg
    except error.IndyError as indy_error:
        if indy_error.error_code is error.ErrorCode.CommonInvalidStructure:
            msg = Message.deserialize(message_bytes)
            msg.context = None
            return msg
        raise indy_error


async def open_wallet(wallet_name, passphrase, ephemeral=False):
    """ Create if not already exists and open wallet.
    """

    wallet_config = json.dumps({"id": wallet_name})
    wallet_credentials = json.dumps({"key": passphrase})

    # Handle ephemeral wallets
    if ephemeral:
        try:
            print("Removing ephemeral wallet.")
            await wallet.delete_wallet(wallet_config, wallet_credentials)
        except error.IndyError as e:
            if e.error_code is error.ErrorCode.WalletNotFoundError:
                pass  # This is ok, and expected.
            else:
                raise e

    try:
        await wallet.create_wallet(wallet_config, wallet_credentials)
    except error.IndyError as e:
        if e.error_code is error.ErrorCode.WalletAlreadyExistsError:
            pass  # This is ok, and expected.
        else:
            raise e

    wallet_handle = await wallet.open_wallet(
        wallet_config,
        wallet_credentials
    )
    return wallet_handle

async def create_and_store_my_did(wallet_handle, **kwargs):
    """ Create and store my DID, adding a map from verkey to DID using the
        non_secrets API.
    """
    (my_did, my_vk) = await did.create_and_store_my_did(wallet_handle, json.dumps(kwargs))

    await non_secrets.add_wallet_record(
        wallet_handle,
        'key-to-did',
        my_vk,
        my_did,
        '{}'
    )

    return my_did, my_vk


async def store_their_did(wallet_handle, their_did, their_vk):
    """ Store their did, adding a map from verkey to DID using the non_secrets
        API.
    """
    await did.store_their_did(
        wallet_handle,
        json.dumps({
            'did': their_did,
            'verkey': their_vk,
        })
    )

    await non_secrets.add_wallet_record(
        wallet_handle,
        'key-to-did',
        their_vk,
        their_did,
        '{}'
    )


async def did_for_key(wallet_handle, key):
    """ Retrieve DID for a given key from the non_secrets verkey to DID map.
    """
    did = None
    try:
        did = json.loads(
            await non_secrets.get_wallet_record(
                wallet_handle,
                'key-to-did',
                key,
                '{}'
            )
        )['value']
    except error.IndyError as e:
        if e.error_code is error.ErrorCode.WalletItemNotFound:
            pass
        else:
            raise e

    return did


async def get_wallet_records(wallet_handle: int, search_type: str) -> list:
    """ Search for records of a given type in a wallet.
    :param wallet_handle: Handle of the wallet to search.
    :param search_type: Type of records to search.
    :return: List of all records found.
    """
    list_of_records = []
    search_handle = await non_secrets.open_wallet_search(wallet_handle,
                                                         search_type,
                                                         json.dumps({}),
                                                         json.dumps({'retrieveTotalCount': True}))
    while True:
        results_json = await non_secrets.fetch_wallet_search_next_records(wallet_handle,
                                                                          search_handle, 10)
        results = json.loads(results_json)

        if results['totalCount'] == 0 or results['records'] is None:
            break
        for record in results['records']:
            record_value = json.loads(record['value'])
            record_value['_id'] = record['id']
            list_of_records.append(record_value)

    await non_secrets.close_wallet_search(search_handle)

    return list_of_records
