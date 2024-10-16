from collections import Counter
import logging
from kademlia_node import Node, NodeHeap
from utils import gather_dict


log = logging.getLogger(__name__)  


class SpiderCrawl:

    def __init__(self, protocol, node, peers, ksize, alpha):

        self.protocol = protocol
        self.ksize = ksize
        self.alpha = alpha
        self.node = node
        self.nearest = NodeHeap(self.node, self.ksize)
        self.last_ids_crawled = []
        log.info("creating spider with peers: %s", peers)
        self.nearest.push(peers)

    async def _find(self, rpcmethod, *args):

        log.info("crawling network with nearest: %s", str(tuple(self.nearest)))
        count = self.alpha
        if self.nearest.get_ids() == self.last_ids_crawled:
            count = len(self.nearest)
        self.last_ids_crawled = self.nearest.get_ids()

        dicts = {}
        for peer in self.nearest.get_uncontacted()[:count]:
            dicts[peer.id] = rpcmethod (peer, self.node, *args)
            self.nearest.mark_contacted(peer)
        found = await gather_dict(dicts)
        return await self._nodes_found(found,*args)

    async def _nodes_found(self, responses, *args):
        raise NotImplementedError

class KeySpiderCrawl(SpiderCrawl):

    def __init__(self, protocol, node, peers, ksize, alpha):
        super().__init__(protocol, node, peers, ksize, alpha)
        self.collected_keys = set()  

    async def find(self):
        return await self._find(self.protocol.call_get_keys)

    async def _nodes_found(self, responses):
        toremove = []
        new_keys = set()

        for peerid, response in responses.items():
            response = RPCGetKeysResponse(response)  
            if not response.happened():
                toremove.append(peerid)
            else:
                new_keys.update(response.get_keys())

        self.collected_keys.update(new_keys)  
        self.nearest.remove(toremove)  

        if self.nearest.have_contacted_all():
            return self.collected_keys
        return await self.find()

class RPCGetKeysResponse:
    def __init__(self, response):
        self.response = response

    def happened(self):
        return self.response[0]

    def get_keys(self):
        return (self.response[1] or ([], []))[0]  
    
    
    def get_node_list(self):
        return (self.response[1] or ([], []))[1]  

class ValueSpiderCrawl(SpiderCrawl):
    def __init__(self, protocol, node, peers, ksize, alpha):
        SpiderCrawl.__init__(self, protocol, node, peers, ksize, alpha)

        self.nearest_without_value = NodeHeap(self.node, 1)

    async def find(self):
        return await self._find(self.protocol.call_find_value)

    async def _nodes_found(self, responses):
  
        toremove = []
        found_values = []
        for peerid, response in responses.items():
            response = RPCFindResponse(response)
            if not response.happened():
                toremove.append(peerid)
            elif response.has_value():
                found_values.append(response.get_value())
            else:
                peer = self.nearest.get_node(peerid)
                self.nearest_without_value.push(peer)
                self.nearest.push(response.get_node_list())
        self.nearest.remove(toremove)

        if found_values:
            return await self._handle_found_values(found_values)
        if self.nearest.have_contacted_all():
            return None
        return await self.find()

    async def _handle_found_values(self, values):
   
        value_counts = Counter(values)
        if len(value_counts) != 1:
            log.warning("Got multiple values for key %i: %s",
                        self.node.long_id, str(values))
        value = value_counts.most_common(1)[0][0]

        peer = self.nearest_without_value.popleft()
        if peer:
            await self.protocol.call_store(peer, self.node.id, value)
        return value


class NodeSpiderCrawl(SpiderCrawl):
    async def find(self):

        return await self._find(self.protocol.call_find_node)

    async def _nodes_found(self, responses):

        toremove = []
        for peerid, response in responses.items():
            response = RPCFindResponse(response)
            if not response.happened():
                toremove.append(peerid)
            else:
                self.nearest.push(response.get_node_list())
        self.nearest.remove(toremove)

        if self.nearest.have_contacted_all():
            return list(self.nearest)
        return await self.find()


class RPCFindResponse:
    def __init__(self, response):

        self.response = response

    def happened(self):
        return self.response[0]

    def has_value(self):
        return isinstance(self.response[1], dict)

    def get_value(self):
        return self.response[1]['value']

    def get_node_list(self):
        nodelist = self.response[1] or []
        return [Node(*nodeple) for nodeple in nodelist]

class SearchByMetadataSpiderCrawl(SpiderCrawl):
    def __init__(self, protocol, node, peers, ksize, alpha):
        super().__init__(protocol, node, peers, ksize, alpha)
        self.collected_keys = set()  

    async def find(self,criteria):
        return await self._find(self.protocol.call_search_by_metadata,criteria)

    async def _nodes_found(self, responses, criteria):
        toremove = []
        new_search = set()

        for peerid, response in responses.items():
            response = RPCGetSearchByMetadataResponse(response)  
            if not response.happened():
                toremove.append(peerid)
            else:
                new_search.update(response.get_found ())

        self.collected_keys.update(new_search) 
        self.nearest.remove(toremove)  

        if self.nearest.have_contacted_all():
            return self.collected_keys
        return await self.find(criteria)
    
class RPCGetSearchByMetadataResponse:

    def __init__(self, response):
        self.response = response

    def happened(self):
        return self.response[0]

    def get_found(self):
        
        return (self.response[1] or ([], []))[0] 

    def get_node_list(self):
        return (self.response[1] or ([], []))[1]  