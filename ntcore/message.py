'''----------------------------------------------------------------------------'''
''' Copyright (c) FIRST 2015. All Rights Reserved.                             '''
''' Open Source Software - may be modified and shared by FRC teams. The code   '''
''' must be accompanied by the FIRST BSD license file in the root directory of '''
''' the project.                                                               '''
'''----------------------------------------------------------------------------'''

#include "Message.h"

#include "Log.h"
#include "WireDecoder.h"
#include "WireEncoder.h"

#define kClearAllMagic 0xD06CB27Aul

import logging
logger = logging.getLogger('nt')

std.shared_ptr<Message> Message.Read(WireDecoder& decoder,
                                       GetEntryTypeFunc get_entry_type)
    unsigned int msg_type
    if not decoder.read8(&msg_type):
        return nullptr

    auto msg =
        std.make_shared<Message>(static_cast<MsgType>(msg_type), private_init())
    switch (msg_type)
    case kKeepAlive:
        break
    case kClientHello:
        unsigned int proto_rev
        if not decoder.read16(&proto_rev):
            return nullptr

        msg.m_id = proto_rev
        # This intentionally uses the provided proto_rev instead of
        # decoder.proto_rev().
        if proto_rev >= 0x0300u:
            if not decoder.readString(&msg.m_str):
                return nullptr


        break

    case kProtoUnsup:
        if not decoder.read16(&msg.m_id):
            return nullptr;    # proto rev

        break

    case kServerHelloDone:
        break
    case kServerHello:
        if decoder.proto_rev() < 0x0300u:
            decoder.set_error("received SERVER_HELLO_DONE in protocol < 3.0")
            return nullptr

        if not decoder.read8(&msg.m_flags):
            return nullptr

        if not decoder.readString(&msg.m_str):
            return nullptr

        break
    case kClientHelloDone:
        if decoder.proto_rev() < 0x0300u:
            decoder.set_error("received CLIENT_HELLO_DONE in protocol < 3.0")
            return nullptr

        break
    case kEntryAssign:
        if not decoder.readString(&msg.m_str):
            return nullptr

        NT_Type type
        if not decoder.readType(&type):
            return nullptr;    # name

        if not decoder.read16(&msg.m_id):
            return nullptr;    # id

        if not decoder.read16(&msg.m_seq_num_uid):
            return nullptr;    # seq num

        if decoder.proto_rev() >= 0x0300u:
            if not decoder.read8(&msg.m_flags):
                return nullptr;    # flags


        msg.m_value = decoder.readValue(type)
        if not msg.m_value:
            return nullptr

        break

    case kEntryUpdate:
        if not decoder.read16(&msg.m_id):
            return nullptr;    # id

        if not decoder.read16(&msg.m_seq_num_uid):
            return nullptr;    # seq num

        NT_Type type
        if decoder.proto_rev() >= 0x0300u:
            if not decoder.readType(&type):
                return nullptr


        else:
            type = get_entry_type(msg.m_id)

        DEBUG4("update message data type: " << type)
        msg.m_value = decoder.readValue(type)
        if not msg.m_value:
            return nullptr

        break

    case kFlagsUpdate:
        if decoder.proto_rev() < 0x0300u:
            decoder.set_error("received FLAGS_UPDATE in protocol < 3.0")
            return nullptr

        if not decoder.read16(&msg.m_id):
            return nullptr

        if not decoder.read8(&msg.m_flags):
            return nullptr

        break

    case kEntryDelete:
        if decoder.proto_rev() < 0x0300u:
            decoder.set_error("received ENTRY_DELETE in protocol < 3.0")
            return nullptr

        if not decoder.read16(&msg.m_id):
            return nullptr

        break

    case kClearEntries:
        if decoder.proto_rev() < 0x0300u:
            decoder.set_error("received CLEAR_ENTRIES in protocol < 3.0")
            return nullptr

        unsigned long magic
        if not decoder.read32(&magic):
            return nullptr

        if magic != kClearAllMagic:
            decoder.set_error(
                "received incorrect CLEAR_ENTRIES magic value, ignoring")
            return nullptr

        break

    case kExecuteRpc:
        if decoder.proto_rev() < 0x0300u:
            decoder.set_error("received EXECUTE_RPC in protocol < 3.0")
            return nullptr

        if not decoder.read16(&msg.m_id):
            return nullptr

        if not decoder.read16(&msg.m_seq_num_uid):
            return nullptr;    # uid

        unsigned long size
        if not decoder.readUleb128(&size):
            return nullptr

         char* params
        if not decoder.read(&params, size):
            return nullptr

        msg.m_str = llvm.StringRef(params, size)
        break

    case kRpcResponse:
        if decoder.proto_rev() < 0x0300u:
            decoder.set_error("received RPC_RESPONSE in protocol < 3.0")
            return nullptr

        if not decoder.read16(&msg.m_id):
            return nullptr

        if not decoder.read16(&msg.m_seq_num_uid):
            return nullptr;    # uid

        unsigned long size
        if not decoder.readUleb128(&size):
            return nullptr

         char* results
        if not decoder.read(&results, size):
            return nullptr

        msg.m_str = llvm.StringRef(results, size)
        break

    default:
        decoder.set_error("unrecognized message type")
        INFO("unrecognized message type: " << msg_type)
        return nullptr

    return msg


def clientHello(self, self_id):
    msg = std.make_shared<Message>(kClientHello, private_init())
    msg.m_str = self_id
    return msg


std.shared_ptr<Message> Message.serverHello(unsigned int flags,
        llvm.StringRef self_id)
    msg = std.make_shared<Message>(kServerHello, private_init())
    msg.m_str = self_id
    msg.m_flags = flags
    return msg


std.shared_ptr<Message> Message.entryAssign(llvm.StringRef name,
        unsigned int id,
        unsigned int seq_num,
        std.shared_ptr<Value> value,
        unsigned int flags)
    msg = std.make_shared<Message>(kEntryAssign, private_init())
    msg.m_str = name
    msg.m_value = value
    msg.m_id = id
    msg.m_flags = flags
    msg.m_seq_num_uid = seq_num
    return msg


std.shared_ptr<Message> Message.entryUpdate(unsigned int id,
        unsigned int seq_num,
        std.shared_ptr<Value> value)
    msg = std.make_shared<Message>(kEntryUpdate, private_init())
    msg.m_value = value
    msg.m_id = id
    msg.m_seq_num_uid = seq_num
    return msg


std.shared_ptr<Message> Message.flagsUpdate(unsigned int id,
        unsigned int flags)
    msg = std.make_shared<Message>(kFlagsUpdate, private_init())
    msg.m_id = id
    msg.m_flags = flags
    return msg


def entryDelete(self, int id):
    msg = std.make_shared<Message>(kEntryDelete, private_init())
    msg.m_id = id
    return msg


std.shared_ptr<Message> Message.executeRpc(unsigned int id, int uid,
        llvm.StringRef params)
    msg = std.make_shared<Message>(kExecuteRpc, private_init())
    msg.m_str = params
    msg.m_id = id
    msg.m_seq_num_uid = uid
    return msg


std.shared_ptr<Message> Message.rpcResponse(unsigned int id, int uid,
        llvm.StringRef results)
    msg = std.make_shared<Message>(kRpcResponse, private_init())
    msg.m_str = results
    msg.m_id = id
    msg.m_seq_num_uid = uid
    return msg


def Write(self, encoder):
    switch (m_type)
    case kKeepAlive:
        encoder.write8(kKeepAlive)
        break
    case kClientHello:
        encoder.write8(kClientHello)
        encoder.write16(encoder.proto_rev())
        if encoder.proto_rev() < 0x0300u:
            return

        encoder.writeString(m_str)
        break
    case kProtoUnsup:
        encoder.write8(kProtoUnsup)
        encoder.write16(encoder.proto_rev())
        break
    case kServerHelloDone:
        encoder.write8(kServerHelloDone)
        break
    case kServerHello:
        if encoder.proto_rev() < 0x0300u:
            return;    # message in version 3.0

        encoder.write8(kServerHello)
        encoder.write8(m_flags)
        encoder.writeString(m_str)
        break
    case kClientHelloDone:
        if encoder.proto_rev() < 0x0300u:
            return;    # message in version 3.0

        encoder.write8(kClientHelloDone)
        break
    case kEntryAssign:
        encoder.write8(kEntryAssign)
        encoder.writeString(m_str)
        encoder.writeType(m_value.type())
        encoder.write16(m_id)
        encoder.write16(m_seq_num_uid)
        if encoder.proto_rev() >= 0x0300u:
            encoder.write8(m_flags)

        encoder.writeValue(*m_value)
        break
    case kEntryUpdate:
        encoder.write8(kEntryUpdate)
        encoder.write16(m_id)
        encoder.write16(m_seq_num_uid)
        if encoder.proto_rev() >= 0x0300u:
            encoder.writeType(m_value.type())

        encoder.writeValue(*m_value)
        break
    case kFlagsUpdate:
        if encoder.proto_rev() < 0x0300u:
            return;    # message in version 3.0

        encoder.write8(kFlagsUpdate)
        encoder.write16(m_id)
        encoder.write8(m_flags)
        break
    case kEntryDelete:
        if encoder.proto_rev() < 0x0300u:
            return;    # message in version 3.0

        encoder.write8(kEntryDelete)
        encoder.write16(m_id)
        break
    case kClearEntries:
        if encoder.proto_rev() < 0x0300u:
            return;    # message in version 3.0

        encoder.write8(kClearEntries)
        encoder.write32(kClearAllMagic)
        break
    case kExecuteRpc:
        if encoder.proto_rev() < 0x0300u:
            return;    # message in version 3.0

        encoder.write8(kExecuteRpc)
        encoder.write16(m_id)
        encoder.write16(m_seq_num_uid)
        encoder.writeString(m_str)
        break
    case kRpcResponse:
        if encoder.proto_rev() < 0x0300u:
            return;    # message in version 3.0

        encoder.write8(kRpcResponse)
        encoder.write16(m_id)
        encoder.write16(m_seq_num_uid)
        encoder.writeString(m_str)
        break
    default:
        break


