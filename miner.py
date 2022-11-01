import blockchain
import time
import new_consensus_module
import output
import encryption_module
import modification


class Miner:
    def __init__(self, address, trans_delay, gossiping):
        self.address = f"Miner_{str(address)}"
        self.top_block = {}
        self.isAuthorized = False
        self.next_pos_block_from = self.address
        self.neighbours = set()
        self.trans_delay = trans_delay/1000
        self.gossiping = gossiping
        self.waiting_times = {}
        self.dpos_vote_for = None
        self.amount_to_be_staked = None
        self.delegates = None
        self.adversary = False
        
        self.local_database={"PREPREAPRE":{"hash_block":{
                                    'vote':0,
                                    'timeStamp':0
                                    }},
                       "PREPARE":{"hash_block":{
                                    'vote':0,
                                    'timeStamp':0
                    }},"COMMIT":{"hash_block":{
                                    'vote':0,
                                    'timeStamp':0
                                }}}

        self.view_number = 0  # Initiated with 1 and increases with each view change
        self.primary_node_id = self.address
        # Dictionary of tuples of accepted preprepare messages: preprepares=[(view_number,sequence_number):digest]
        self.preprepare_messages = None
        self.preprepares = {}
        self.prepared_messages = []  # set of prepared messages
        # Maintain a dictionary of the last reply for each client: replies={client_id_1:[last_request_1,last_reply_1],...}
        self.replies = {}
        self.message_reply = []  # List of all the reply messages
        # Dictionary of accepted prepare messages: prepares = {(view_number,sequence_number,digest):[different_nodes_that_replied]}
        self.all = {}
        self.preprepare=[] #local chain
        # Dictionary of accepted commit messages: commits = {(view_number,sequence_number,digest):[different_nodes_that_replied]}
        self.commits = {}
        self.message_log = []  # Set of accepted messages
        # A dictionary that for each client, stores the timestamp of the last reply
        self.last_reply_timestamp = {}
        # Dictionary of checkpoints: {checkpoint:[list_of_nodes_that_voted]}
        self.checkpoints = {}
        self.status=None
        processed_messages = []
        # List of sequence numbers where a checkpoint was proposed
        self.checkpoints_sequence_number = []
        self.stable_checkpoint = {"message_type": "CHECKPOINT", "sequence_number": 0,
                                  "checkpoint_digest": "the_checkpoint_digest", "node_id": self.address}  # The last stable checkpoint
        # list of nodes that voted for the last stable checkpoint
        self.stable_checkpoint_validators = []
        self.h = 0  # The low water mark = sequence number of the last stable checkpoint
        self.H = self.h + 200  # The high watermark, proposed value in the original article
        # This is a dictionary of the accepted preprepare messages with the time they were accepted so that one the timer is reached, the node starts a wiew change. The dictionary has the form : {"request":starting_time...}. the request is discarded once it is executed.
        self.accepted_requests_time = {}
        # This is a dictionary of the accepted preprepare messages with the time they were replied to. The dictionary has the form : {"request": ["reply",replying_time]...}. the request is discarded once it is executed.
        self.replies_time = {}
        # Dictionary of received view-change messages (+ the view change the node itself sent) if the node is the primary node in the new view, it has the form: {new_view_number:[list_of_view_change_messages]}
        self.received_view_changes = {}
        self.asked_view_change = []  # view numbers the node asked for
        global n
        n=0
        global f
        f = (n - 1) // 3
        

    def build_block(self, num_of_tx_per_block, mempool, miner_list, type_of_consensus, blockchain_function, expected_chain_length, AI_assisted_mining_wanted):
        if type_of_consensus == 3 and not self.isAuthorized:
            output.unauthorized_miner_msg(self.address)
        elif type_of_consensus == 4:
            waiting_time = (self.top_block['Body']['timestamp'] +
                            self.waiting_times[self.top_block['Header']['blockNo'] + 1]) - time.time()
            if waiting_time <= 0:
                self.continue_building_block(num_of_tx_per_block, mempool, miner_list, type_of_consensus,
                                             blockchain_function, expected_chain_length, AI_assisted_mining_wanted)
        
        else:
            self.continue_building_block(num_of_tx_per_block, mempool, miner_list, type_of_consensus,
                                         blockchain_function, expected_chain_length, AI_assisted_mining_wanted)

    def continue_building_block(self, num_of_tx_per_block, mempool, miner_list, type_of_consensus, blockchain_function, expected_chain_length, AI_assisted_mining_wanted):
        if accumulated_transactions := new_consensus_module.accumulate_transactions(num_of_tx_per_block, mempool, blockchain_function, self.address):
            transactions = accumulated_transactions
            new_block = self.abstract_block_building(
                blockchain_function, transactions, miner_list, type_of_consensus, AI_assisted_mining_wanted)
            output.block_info(new_block, type_of_consensus)
            time.sleep(self.trans_delay)
            for elem in miner_list:
                if elem.address in self.neighbours:
                    elem.receive_new_block(new_block, type_of_consensus, miner_list, blockchain_function,
                                           expected_chain_length)

    def abstract_block_building(self, blockchain_function, transactions, miner_list, type_of_consensus, AI_assisted_mining_wanted):
        if blockchain_function == 3:
            transactions = self.validate_transactions(
                transactions, "generator")
        if self.gossiping:
            self.gossip(blockchain_function, miner_list)
        new_block = new_consensus_module.generate_new_block(transactions, self.address,
                                                            self.top_block['Header']['hash'], type_of_consensus,
                                                            AI_assisted_mining_wanted, self.adversary)
        if type_of_consensus == 4:
            new_block['Header']['PoET'] = encryption_module.retrieve_signature_from_saved_key(
                new_block['Body']['previous_hash'], self.address)
        if type_of_consensus == 6:
           
            new_block['Header']['status'] = 'PREPREPARE'
            self.preprepares[new_block['Header']['hash']]={'prepare':0,
                                                           'commit':0,
                                                           'time':time.time()}
            
        return new_block
    
    
    

    def receive_new_block(self, new_block, type_of_consensus, miner_list, blockchain_function, expected_chain_length):
        block_already_received = False
        local_chain_temporary_file = modification.read_file(str(f"temporary/{self.address}_local_chain.json"))

        condition_1 = (len(local_chain_temporary_file) == 0) and (
            new_block['Header']['generator_id'] == 'The Network')
        if condition_1:
            self.add(new_block, blockchain_function,
                     expected_chain_length, miner_list,type_of_consensus)
        else:
            if self.gossiping:
                self.gossip(blockchain_function, miner_list)
            list_of_hashes_in_local_chain = []
            for key in local_chain_temporary_file:
                read_hash = local_chain_temporary_file[key]['Header']['hash']
                list_of_hashes_in_local_chain.append(read_hash)
                if new_block['Header']['hash'] == read_hash:
                    block_already_received = True
                    break
            if not block_already_received and new_consensus_module.block_is_valid(type_of_consensus, new_block, self.top_block, self.next_pos_block_from, miner_list, self.delegates):
                self.add(new_block, blockchain_function,
                         expected_chain_length, miner_list,type_of_consensus)
                time.sleep(self.trans_delay)
                for elem in miner_list:
                    if elem.address in self.neighbours:
                        elem.receive_new_block(
                            new_block, type_of_consensus, miner_list, blockchain_function, expected_chain_length)

    def validate_transactions(self, list_of_new_transactions, miner_role):
        user_wallets_temporary_file = modification.read_file(str(f"temporary/{self.address}_users_wallets.json"))

        if list_of_new_transactions:
            for key in user_wallets_temporary_file:
                for transaction in list_of_new_transactions:
                    if miner_role == "receiver":
                        if key == f"{str(transaction[1])}.{str(transaction[2])}":
                            if user_wallets_temporary_file[key]['wallet_value'] >= transaction[0]:
                                user_wallets_temporary_file[key]['wallet_value'] -= transaction[0]
                            else:
                                return False
                        if key == f"{str(transaction[3])}.{str(transaction[4])}":
                            user_wallets_temporary_file[key]['wallet_value'] += transaction[0]
                    if miner_role == "generator" and key == f"{str(transaction[1])}.{str(transaction[2])}" and user_wallets_temporary_file[key]['wallet_value'] < transaction[0]:
                        output.illegal_tx(
                            transaction, user_wallets_temporary_file[key]['wallet_value'])
                        del transaction
        if miner_role == "generator":
            return list_of_new_transactions
        if miner_role == "receiver":
            modification.rewrite_file(str(f"temporary/{self.address}_users_wallets.json"), user_wallets_temporary_file)

            return True
        
        
    
    def get_f():
        
        return f
    def gen_time():
        return time.time()
        
      

    def bft_respond(self,block,list_of_miners):  
        
        recvied_message = block['Header']['status']
        
        
        if recvied_message !="PREPREPARE" and recvied_message["Header"]['hash'] != self.top_block['Header']['hash']:
            return False
        elif  recvied_message =="PREPREPARE":
             address_id=recvied_message["Header"]["generator_id"]
             actual_timestamp=self.top_block['Header']['timestamp']
             timestamp = recvied_message["timestamp"]=self.gen_time()
             if actual_timestamp >= timestamp:
                 for database in self.local_database:
                    database['PREPREAPRE']['vote']+=1
                    database['PREPREAPRE']['time']=timestamp
             else:
                 
                return False             
             
        elif recvied_message !="PREPARE" or recvied_message['Header']["hash"] != self.top_block['Header']['hash']or self.top_block['Header']['timestamp']< timestamp:
            return False
        elif recvied_message =="PREPARE":
            address_id=recvied_message["Header"]["generator_id"]
            actual_timestamp=self.top_block['Header']['timestamp']
            timestamp = recvied_message["timestamp"]=self.gen_time()
            if actual_timestamp >= timestamp and  len(self.local_database) > self.get_f() * (len(list_of_miners) - 1):
                for database in self.local_database:
                    database['PREAPRE']['vote']+=2
                    database['PREAPRE']['time']=timestamp
            else:
                 
                return False 
               
        elif recvied_message !="Commit"  or recvied_message["timestamp"] <= self.top_block['Header']['timestamp']:
            if self.prepared_messages != self.get_f:
                 return False
            return False
        else:
            address_id=recvied_message["Header"]["generator_id"]
            actual_timestamp=self.top_block['Header']['timestamp']
            timestamp = recvied_message["timestamp"]=self.gen_time()
            if actual_timestamp >= timestamp: 
                if self.leader == address_id and self.prepared_messages == self.get_f:
                
                    for database in self.local_database:
                        database['COMMIT']['vote']+=3
                        database['COMMIT']['time']=timestamp
                    return True
                else:
                     return False
            
            return False
           
                        
        #if status =="preprepare"
        #main part algorithm should 
        #if type comiit  
            #if the miner was leader it is need to add mnig is block
    
    def add(self, block, blockchain_function, expected_chain_length, list_of_miners,type_of_consensus):
        ready = False
        local_chain_temporary_file = modification.read_file(f"temporary/{self.address}_local_chain.json")

        if len(local_chain_temporary_file) == 0:
            ready = True
        else:
            condition = blockchain_function == 3 and self.validate_transactions(
                block['Body']['transactions'], "receiver")
            if (blockchain_function != 3 or condition) and block['Body']['previous_hash'] == self.top_block['Header']['hash']:
                if type_of_consensus == 6:
                    ready = self.bft_respond(block,list_of_miners)
                else:
                    blockchain.report_a_successful_block_addition(
                    block['Header']['generator_id'], block['Header']['hash'])
                    ready=True
        if ready:
            block['Header']['blockNo'] = len(local_chain_temporary_file)
            self.top_block = block
            local_chain_temporary_file[str(
                len(local_chain_temporary_file))] = block
            modification.rewrite_file(str(f"temporary/{self.address}_local_chain.json"), local_chain_temporary_file)

            if self.gossiping:
                self.update_global_longest_chain(
                    local_chain_temporary_file, blockchain_function, list_of_miners)

    def gossip(self, blockchain_function, list_of_miners):
        local_chain_temporary_file = modification.read_file(str(f"temporary/{self.address}_local_chain.json"))

        temporary_global_longest_chain = modification.read_file(
            'temporary/longest_chain.json')
        condition_1 = len(temporary_global_longest_chain['chain']) > len(
            local_chain_temporary_file)
        condition_2 = self.global_chain_is_confirmed_by_majority(
            temporary_global_longest_chain['chain'], len(list_of_miners))
        if condition_1 and condition_2:
            confirmed_chain = temporary_global_longest_chain['chain']
            confirmed_chain_from = temporary_global_longest_chain['from']
            modification.rewrite_file(str(f"temporary/{self.address}_local_chain.json"), confirmed_chain)

            self.top_block = confirmed_chain[str(len(confirmed_chain) - 1)]
            output.local_chain_is_updated(self.address, len(confirmed_chain))
            if blockchain_function == 3:
                user_wallets_temp_file = modification.read_file(str(f"temporary/{confirmed_chain_from}_users_wallets.json"))

                modification.rewrite_file(str(f"temporary/{self.address}_users_wallets.json"), user_wallets_temp_file)

    def global_chain_is_confirmed_by_majority(self, global_chain, no_of_miners):
        chain_is_confirmed = True
        temporary_confirmations_log = modification.read_file(
            'temporary/confirmation_log.json')
        for block in global_chain:
            condition_0 = block != '0'
            if condition_0:
                condition_1 = global_chain[block]['Header']['hash'] not in temporary_confirmations_log

                if condition_1:
                    chain_is_confirmed = False
                    break
                else:
                    condition_2 = temporary_confirmations_log[global_chain[block]['Header']['hash']]['votes'] <= (
                        no_of_miners / 2)
                    if condition_2:
                        chain_is_confirmed = False
                        break
        return chain_is_confirmed

    def update_global_longest_chain(self, local_chain_temporary_file, blockchain_function, list_of_miners):
        temporary_global_longest_chain = modification.read_file(
            'temporary/longest_chain.json')
        if len(temporary_global_longest_chain['chain']) < len(local_chain_temporary_file):
            temporary_global_longest_chain['chain'] = local_chain_temporary_file
            temporary_global_longest_chain['from'] = self.address
            modification.rewrite_file(
                'temporary/longest_chain.json', temporary_global_longest_chain)
        elif len(temporary_global_longest_chain['chain']) > len(local_chain_temporary_file) and self.gossiping:
            self.gossip(blockchain_function, list_of_miners)

