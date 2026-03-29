
# Kvon Distributed Network Protocol

## registration

1. new peer (newborn) send REGISTER prompt to any of peers in network (advisor)
    - advisor adds newborn address to it's local routing table
    - and sends WELCOME prompt with it's routing table back to newborn

2. newborn gets WELCOME prompt back
    - newborn adds all local peers to it's local routing table
    - newborn adds all next peers to it's next routing table

3. newborn broadcasts NEWBORN prompt to all local peers (neighbours)
    - all neighbours add newborn to their routing table
    - all peers, reply with PONG prompt to newborn
    - newborn now can process messages

## keepalive

1. each peer (pinger) every some time (tens of seconds) sends PING prompt
   to oldest peer (gaffer) on it's local and next routing tables (peer with
   most time without any message to/from)
    - if gaffer did not answer - remove it from pinger's routing table
      and try again with next oldest peer in local routing table

1. each peer (checker) every some time (minutes) sends GETPEERS prompt
   to oldest peer on it's local routing table (gaffer)
    - if gaffer did not answer - remove it from checker's local routing table
      and try again with next oldest peer in checker's routing table
    - if gaffer's keyrange in PEERS prompt differs from checker's keyrange,
      then remove gaffer from checker's local routing table
    - if gaffer's keyrange matches checker's keyrange - add all peers from
      PEERS prompt (neighbours) to checker's local routing table

2. each peer (checker) every some time (minutes) sends GETPEERS prompt
   to oldest peer (nextgaffer) on it's next routing table
    - if nextgaffer did not answer - remove it from checker's next routing
      table and try again with next oldest peer in next routing table
    - if nextgaffer's keyrange in PEERS prompt is not adjacent to checker's
      keyrange, then remove nextgaffer from checker's next routing table
    - if next's keyrange is adjacent to checker's keyrange - add all peers
      from PEERS prompt (nexts) to checker's next routing table

## splitting

1. If any peer (splitter) sees number of peers in local slot become larger
   than MAX_SLOT_PEERS, after getting a NEWBORN prompt
    - begin slot splitting procedure

2. Order all peers (neighbours) from local routing table on single list.
    - Based of splitter index in ordered list
    - if splitter in left half of ordered list
       - splitter change it's own keyrange to low half of it
       - change local routing table to low half of ordered list
       - change next routing table to high half or routing list
       - remove entries from data storage, that does not fit in updated keyrange
    - if splitter in right half (or middle) of ordered list
       - splitter change it's own keyrange to high half of it
       - change local routing table to high half of ordered list
       - remove entries from data storage, that does not fit in updated keyrange

## merging

1. If any peer (merger) sees number of peers in local split become smaller
   than MIN_SLOT_PEERS after removing some peer (leaver) from local
   routing table
    - merger checks if
       `size(local routing table) + size(next routing table) < MAX_SLOT_PEERS`
    - if it is true - begin merging procedure (else begin borrowing procedure)
       - merger send MERGEREQUEST to any peer from next routing table (next)
       - next sends back WELCOME prompt and next adds merger to it's local
         routing table
       - then merger updates it's keyrange, local routing table and next
         routing table onees from WELCOME prompt
       - then merger sends NEWBORN prompt to all peers (neighbours) from
         it's new local routing table
       - then merger sends LEFT prompt to all old peers (old neighbours),
         and with old KEYRANGE field (before WELCOME prompt) and with leaver as
         PEER field
       - when old neighbours get LEFT prompt - they check themselves that
         leaver is offline
       - if it is offline - they also do the same steps as merger before

## borrowing

1. If any peer (borrower) sees number of peers in local split become smaller
   than MIN_SLOT_PEERS after removing some peer (leaver) from local
   routing table
    - borrower checks if
       `size(local routing table) + size(next routing table) < MAX_SLOT_PEERS`
    - if it is false - begin borrowing procedure (else begin merging procedure):
      - borrower orders all peers from next routing table, and picks the first
        one by order (itinerant)
      - borrower sends BORROWREQUEST prompt to itinerant
      - itinerant changes it's next routing table to local routing table, and
        changes local routing table to peers from BORROWREQUEST prompt
      - itinerant changes it's keyrange to keyrange from BORROWREQUEST
      - itinerant clears keys from it's data storage
      - itinerant sends NEWBORN to all it's new local peers

--------------------------------------------------------------------------------

class Peer:
 - address: [ip, port]
 - keyRange: [hash, hash]
 - localPeers: set[Peer]
 - nextPeers: set[Peer]
 - dataStorage: dict[key, value]

send_prompt(peer, prompt):
 - send prompt to peer

broadcast_prompt(prompt):
 - send prompt to all local slot peers

-------------------------------------------------------------------------------

## registration prompts

REGISTER prompt:
 - TYPE: enum: prompt type
 - NAME: str: name of client
reply: WELCOME

WELCOME prompt:
 - TYPE: enum: prompt type
 - KEYRANGE: hash, hash: prompt sender's range of keys
 - PEERCOUNT: int: number of local peers in prompt
 - PEER+: str, int: peer ip, peer port
 - NEXTCOUNT: int: number of next peers in prompt
 - NEXT+: str, int: next peer ip, next peer port
reply: None

NEWBORN prompt:
 - TYPE: enum: prompt type
 - KEYRANGE: hash, hash: prompt sender's range of keys
reply: PONG

## keepalive prompts

PING prompt:
 - TYPE: enum: prompt type
reply: PONG

PONG prompt:
 - TYPE: enum: prompt type
 - KEYRANGE: hash, hash: range of keys
reply: None

GETPEERS prompt:
 - TYPE: enum: prompt type
reply: PEERS

PEERS prompt:
 - TYPE: enum: prompt type
 - KEYRANGE: hash, hash: range of keys
 - COUNT: int: number of local peers in prompt
 - PEER+: str, int: peer ip, peer port
reply: None

## borrow-merge prompts

MERGEREQUEST prompt:
 - TYPE: enum prompt type
 - KEYRANGE: hash, hash: range or keys
reply: WELCOME

BORROWREQUEST prompt:
 - TYPE: enum prompt type
 - KEYRANGE: hash, hash: range of keys of prompt sender
 - COUNT: int: number of local peers in prompt
 - PEER+: str, int: peer ip, peer port
reply: None

LEFT prompt:
 - TYPE: enum: prompt type
 - KEYRANGE: hash, hash: range of keys
 - PEER: str, int: peer ip, peer port


-------------------------------------------------------------------------------
