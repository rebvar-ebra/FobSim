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
        self.trans_delay = trans_delay / 1000
        self.gossiping = gossiping
        self.waiting_times = {}
        self.dpos_vote_for = None
        self.amount_to_be_staked = None
        self.delegates = None
        self.adversary = False
        self.waiting = 2
        self.leader = None
        self.local_database = {"PREPREPARE": {},
                               "PREPARE": {},
                               "COMMIT": {}}

        self.primary_node_id = self.address
        global n
        n = 0
        global f
        f = (n - 1) / 3

    def build_block(self, num_of_tx_per_block, mempool, miner_list, type_of_consensus, blockchain_function,
                    expected_chain_length, AI_assisted_mining_wanted):
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

    def continue_building_block(self, num_of_tx_per_block, mempool, miner_list, type_of_consensus, blockchain_function,
                                expected_chain_length, AI_assisted_mining_wanted):
        if accumulated_transactions := new_consensus_module.accumulate_transactions(num_of_tx_per_block, mempool,
                                                                                    blockchain_function, self.address):
            transactions = accumulated_transactions
            new_block = self.abstract_block_building(
                blockchain_function, transactions, miner_list, type_of_consensus, AI_assisted_mining_wanted)
            output.block_info(new_block, type_of_consensus)
            time.sleep(self.trans_delay)
            for elem in miner_list:
                if elem.address in self.neighbours:
                    elem.receive_new_block(new_block, type_of_consensus, miner_list, blockchain_function,
                                           expected_chain_length)

    def abstract_block_building(self, blockchain_function, transactions, miner_list, type_of_consensus,
                                AI_assisted_mining_wanted):
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
            #self.local_database[new_block['Header']['hash']] = {'PREPARE': 0,'COMMIT': 0,'time': time.time()}

        return new_block

    def receive_new_block(self, new_block, type_of_consensus, miner_list, blockchain_function, expected_chain_length):
        block_already_received = False
        local_chain_temporary_file = modification.read_file(str(f"temporary/{self.address}_local_chain.json"))

        condition_1 = (len(local_chain_temporary_file) == 0) and (
                new_block['Header']['generator_id'] == 'The Network')
        if condition_1:
            self.add(new_block, blockchain_function,
                     expected_chain_length, miner_list, type_of_consensus)
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
            if not block_already_received and new_consensus_module.block_is_valid(type_of_consensus, new_block,
                                                                                  self.top_block,
                                                                                  self.next_pos_block_from, miner_list,
                                                                                  self.delegates):
                self.add(new_block, blockchain_function,
                         expected_chain_length, miner_list, type_of_consensus)
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
                    if miner_role == "generator" and key == f"{str(transaction[1])}.{str(transaction[2])}" and \
                            user_wallets_temporary_file[key]['wallet_value'] < transaction[0]:
                        output.illegal_tx(
                            transaction, user_wallets_temporary_file[key]['wallet_value'])
                        del transaction
        if miner_role == "generator":
            return list_of_new_transactions
        if miner_role == "receiver":
            modification.rewrite_file(str(f"temporary/{self.address}_users_wallets.json"), user_wallets_temporary_file)

            return True

    def get_f(self):
        return 2 * f + 1


    def bft_respond(self, new_block, miner_list, blockchain_function, expected_chain_length):

            recevied_message = new_block['Header']['status']
            key=encryption_module.generate_PKI_keys(64,self.address)
            public_key=modification.read_file(f"temporary/{key}_public.key")
            if recevied_message == 'PREPREPARE':
                address_id = new_block['Header']['generator_id']
                get_hash = new_block['Header']['hash']
                timestamp_difference = new_block['Body']['timestamp'] - time.time()
                block_info = {'votes': 1,
                              'timestamp': new_block['Body']['timestamp'],
                              'broadcast': False,
                              }
                if get_hash in self.block_received(new_block,recevied_message):#check block exist
                    if public_key == self.address: #check vote before
                        return False
                    else:
                        self.local_database['PREPREPARE'][get_hash]=block_info
                        block_info['votes']=block_info['votes']+1
                        self.local_database['PREPARE'][get_hash]=block_info
                        block_info['votes'] = block_info['votes'] + 1
                else:#check receive new block
                    if timestamp_difference <= self.waiting and self.leader == address_id:
                        self.block_received(new_block, new_block['Header']['status'])
                        self.local_database['PREPARE'][get_hash] = block_info
                        block_info['votes'] = block_info['votes'] + 1
                    else:
                        return False
                    if self.local_database[recevied_message][get_hash]['votes'] > self.get_f():#check the majority
                        new_block['Header']['status'] = 'PREPARE'
                        check_broadcast= self.local_database[new_block][get_hash][block_info]['broadcast']
                        for brodcast in check_broadcast:
                            if brodcast != False:
                                return False
                            else:
                                for miner in miner_list:
                                    if miner.address in self.neighbours:
                                        miner.local_database[recevied_message][get_hash] + block_info
                                        miner.local_database['PREPARE'][get_hash] + block_info
                                        miner.receive_new_block(new_block, 6, miner_list, blockchain_function,
                                                               expected_chain_length)
                    else:
                        check_broadcast= self.local_database[recevied_message][get_hash][block_info]['broadcast']
                        for brodcast in check_broadcast:
                            if brodcast != False:
                                return False
                            else:
                                for miner in miner_list:
                                    if miner.address in self.neighbours:
                                        miner.local_database[recevied_message][get_hash] + block_info
                                        miner.receive_new_block(new_block, 6, miner_list, blockchain_function,
                                                               expected_chain_length)
                                    else:
                                        return  False

            elif recevied_message == 'PREPARE':
                address_id = new_block['Header']['generator_id']
                get_hash = new_block['Header']['hash']
                timestamp_difference = self.block_timestamp(get_hash) - time.time()
                if timestamp_difference <= self.waiting and self.leader == address_id and get_hash in self.local_database['PREPARE']:
                    self.local_database['PREPARE'][get_hash]['votes'] += 1
                    if len(self.local_database['PREPARE'][get_hash]['votes']) > self.get_f() * len(miner_list) - 1:

                        block_info = {'votes': 1,
                                      'timestamp': new_block['Body']['timestamp'],
                                      'broadcast': False
                                      }
                        self.local_database['COMMIT'][get_hash] = block_info
                        block_info['votes'] = block_info['votes'] + 1
                        self.local_database[recevied_message][get_hash] = block_info

                        new_block['Header']['status'] = 'COMMIT'
                        for elem in miner_list:
                            if elem.address in self.neighbours:
                                elem.receive_new_block(
                                    new_block, 6, miner_list, blockchain_function, expected_chain_length)
            elif recevied_message == 'COMMIT':
                address_id = new_block['Header']['generator_id']
                get_hash = new_block['Header']['hash']
                timestamp_difference = self.block_timestamp(get_hash) - time.time()
                if timestamp_difference <= self.waiting and self.leader == address_id and get_hash in self.local_database['COMMIT']:
                    self.local_database['COMMIT'][get_hash]['votes'] += 1
                    if len(self.local_database['COMMIT'][get_hash]['votes']) > self.get_f() * len(miner_list) - 1:
                        if get_hash not in self.local_database['COMMIT']:
                            self.add(new_block, blockchain_function, expected_chain_length, miner_list, 6)
                        else:
                            self.local_database['COMMIT'][get_hash]['votes'] += 1


                        if self.leader != self.address:
                            for elem in miner_list:
                                if elem.address == self.leader:
                                    elem.receive_new_block(
                                        new_block, 6, miner_list, blockchain_function, expected_chain_length)
                                    break


    def block_received(self, new_block, status):
        result = False

        for _ in self.local_database:
            try:
                if self.local_database[status]['hash_block'] == new_block['Header']['hash']:
                    return True
            except Exception as e:
                return result

    def block_timestamp(self, get_h):

        return self.local_database['PREPREPARE'][get_h]['timestamp']


    def add(self, block, blockchain_function, expected_chain_length, list_of_miners, type_of_consensus):
        ready = False
        local_chain_temporary_file = modification.read_file(f"temporary/{self.address}_local_chain.json")

        if len(local_chain_temporary_file) == 0:
            ready = True
        else:
            condition = blockchain_function == 3 and self.validate_transactions(
                block['Body']['transactions'], "receiver")
            if (blockchain_function != 3 or condition) and block['Body']['previous_hash'] == self.top_block['Header'][
                'hash']:
                if type_of_consensus == 6:

                    self.bft_respond(block,list_of_miners,blockchain_function,expected_chain_length)

                    ready = True
                else:
                    blockchain.report_a_successful_block_addition(
                        block['Header']['generator_id'], block['Header']['hash'])
                    ready = True
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
                user_wallets_temp_file = modification.read_file(
                    str(f"temporary/{confirmed_chain_from}_users_wallets.json"))

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
