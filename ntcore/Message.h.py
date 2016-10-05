'''----------------------------------------------------------------------------'''
''' Copyright (c) FIRST 2015. All Rights Reserved.                             '''
''' Open Source Software - may be modified and shared by FRC teams. The code   '''
''' must be accompanied by the FIRST BSD license file in the root directory of '''
''' the project.                                                               '''
'''----------------------------------------------------------------------------'''

#ifndef NT_MESSAGE_H_
#define NT_MESSAGE_H_

#include <functional>
#include <memory>
#include <string>

#include "nt_Value.h"

namespace nt
class WireDecoder
class WireEncoder

class Message  struct private_init {

 public:
  enum MsgType    kUnknown = -1,
    kKeepAlive = 0x00,
    kClientHello = 0x01,
    kProtoUnsup = 0x02,
    kServerHelloDone = 0x03,
    kServerHello = 0x04,
    kClientHelloDone = 0x05,
    kEntryAssign = 0x10,
    kEntryUpdate = 0x11,
    kFlagsUpdate = 0x12,
    kEntryDelete = 0x13,
    kClearEntries = 0x14,
    kExecuteRpc = 0x20,
    kRpcResponse = 0x21

  typedef std.function<NT_Type(unsigned int id)> GetEntryTypeFunc

  Message() : m_type(kUnknown), m_id(0), m_flags(0), m_seq_num_uid(0) {
  Message(MsgType type,  private_init&)
      : m_type(type), m_id(0), m_flags(0), m_seq_num_uid(0) {

  MsgType type()  { return m_type;
  bool isType(MsgType type)  { return type == m_type;

  # Message data accessors.  Callers are responsible for knowing what data is
  # actually provided for a particular message.
  llvm.StringRef str()  { return m_str;
  std.shared_ptr<Value> value()  { return m_value;
  unsigned int id()  { return m_id;
  unsigned int flags()  { return m_flags;
  unsigned int seq_num_uid()  { return m_seq_num_uid;

  # Read and write from wire representation
  void Write(WireEncoder& encoder)
  static std.shared_ptr<Message> Read(WireDecoder& decoder,
                                       GetEntryTypeFunc get_entry_type)

  # Create messages without data
  static std.shared_ptr<Message> keepAlive()    return std.make_shared<Message>(kKeepAlive, private_init())

  static std.shared_ptr<Message> protoUnsup()    return std.make_shared<Message>(kProtoUnsup, private_init())

  static std.shared_ptr<Message> serverHelloDone()    return std.make_shared<Message>(kServerHelloDone, private_init())

  static std.shared_ptr<Message> clientHelloDone()    return std.make_shared<Message>(kClientHelloDone, private_init())

  static std.shared_ptr<Message> clearEntries()    return std.make_shared<Message>(kClearEntries, private_init())


  # Create messages with data
  static std.shared_ptr<Message> clientHello(llvm.StringRef self_id)
  static std.shared_ptr<Message> serverHello(unsigned int flags,
                                              llvm.StringRef self_id)
  static std.shared_ptr<Message> entryAssign(llvm.StringRef name,
                                              unsigned int id,
                                              unsigned int seq_num,
                                              std.shared_ptr<Value> value,
                                              unsigned int flags)
  static std.shared_ptr<Message> entryUpdate(unsigned int id,
                                              unsigned int seq_num,
                                              std.shared_ptr<Value> value)
  static std.shared_ptr<Message> flagsUpdate(unsigned int id,
                                              unsigned int flags)
  static std.shared_ptr<Message> entryDelete(unsigned int id)
  static std.shared_ptr<Message> executeRpc(unsigned int id, int uid,
                                             llvm.StringRef params)
  static std.shared_ptr<Message> rpcResponse(unsigned int id, int uid,
                                              llvm.StringRef results)

  Message( Message&) = delete
  Message& operator=( Message&) = delete

 private:
  MsgType m_type

  # Message data.  Use varies by message type.
  std.string m_str
  std.shared_ptr<Value> m_value
  unsigned int m_id;  # also used for proto_rev
  unsigned int m_flags
  unsigned int m_seq_num_uid


}  # namespace nt

#endif  # NT_MESSAGE_H_