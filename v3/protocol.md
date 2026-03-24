
1. client sends REGISTER prompt to randezvous server
2. client gets online peers from randezvous server by PEERS prompt

3. client gets current chat state by sending prompt GETCHATHEAD to peer
4. client constructs local message chain by receiving CHATHEAD prompt

5. client tries to send message to peer with POST prompt
6. client gets status of sending attempt with POSTSTATUS prompt



REGISTER prompt:
 - HEADER: enum: prompt type
 - NAME: str, name of client
reply: PEERS

PEERS prompt:
 - HEADER: enum: prompt type
 - COUNT: int: number of peers in prompt
 - PEER*: str, int: peer ip, peer port
reply: None

GETCHATHEAD prompt:
 - HEADER: enum: prompt type
 - NAME: str: name of peer to get chat head from
reply: CHATHEAD

CHATHEAD prompt:
 - HEADER: enum: prompt type
 - NAME: str: name of peer of which chat is this head
 - MESSAGEID: hash: id of message of head of chat
reply: None

POST::TEXT prompt:
 - HEADER: enum: prompt type
 - CHATID: hash: id of chat to send message to
 - TIMESTAMP: timestamp: time when prompt was created
 - MSGID: hash: hash of message
 - MSGHEADER: enum: message type {TEXT}
 - DATA: str: message data
reply: COMMIT, EAGAIN

EAGAIN prompt:
 - HEADER: enum: prompt type
 - CHATID: hash: id of chat, prompt to which failed

COMMIT prompt:
 - HEADER: enum: prompt type
 - CHATID: hash: id of chat, where commit was made
 - MSGID: hash: hash of message
