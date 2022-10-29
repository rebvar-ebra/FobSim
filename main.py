from ast import Pass
from multiprocessing import Process
import Fog
import end_user
import miner
import blockchain
import random
import output
from math import ceil
import time
import modification
import new_consensus_module


data = modification.read_file("Sim_parameters.json")
list_of_end_users = []
fogNodes = []
transactions_list = []
list_of_authorized_miners = []
blockchainFunction = 0
blockchainPlacement = 0
number_of_miner_neighbours = data["number_of_each_miner_neighbours"]
NumOfFogNodes = data["NumOfFogNodes"]
NumOfTaskPerUser = data["NumOfTaskPerUser"]
NumOfMiners = data["NumOfMiners"]
numOfTXperBlock = data["numOfTXperBlock"]
num_of_users_per_fog_node = data["num_of_users_per_fog_node"]
blockchain_functions = ['1', '2', '3', '4']
blockchain_placement_options = ['1', '2']
expected_chain_length = ceil((num_of_users_per_fog_node * NumOfTaskPerUser * NumOfFogNodes) / numOfTXperBlock)
gossip_activated = data["Gossip_Activated"]
Automatic_PoA_miners_authorization = data["Automatic_PoA_miners_authorization?"]
Parallel_PoW_mining = data["Parallel_PoW_mining?"]
trans_delay = 0
delay_between_fog_nodes = data["delay_between_fog_nodes"]
delay_between_end_users = data["delay_between_end_users"]
poet_block_time = data['poet_block_time']
Asymmetric_key_length = data['Asymmetric_key_length']
number_of_DPoS_delegates = data['Num_of_DPoS_delegates']
user_informed = False


def user_input():
    modification.initiate_files(gossip_activated)
    choose_functionality()
    choose_placement()


def choose_functionality():
    while True:
        output.choose_functionality()
        global blockchainFunction
        blockchainFunction = input()
        if blockchainFunction in blockchain_functions:
            blockchainFunction = int(blockchainFunction)
            break
        else:
            print("Input is incorrect, try again..!")


def choose_placement():
    while True:
        output.choose_placement()
        global blockchainPlacement
        blockchainPlacement = input()
        if blockchainPlacement in blockchain_placement_options:
            blockchainPlacement = int(blockchainPlacement)
            break
        else:
            print("Input is incorrect, try again..!")


def initiate_network():
    for count in range(NumOfFogNodes):
        fogNodes.append(Fog.Fog(count + 1))
        for p in range(num_of_users_per_fog_node):
            list_of_end_users.append(end_user.User(p + 1, count + 1))
    output.users_and_fogs_are_up()
    if blockchainFunction == 4:
        output.GDPR_warning()
        while True:
            print("If you don't want other attributes to be added to end_users, input: done\n")
            new_attribute = input("If you want other attributes to be added to end_users, input them next:\n")
            if new_attribute == 'done':
                break
            else:
                for user in list_of_end_users:
                    user.identity_added_attributes[new_attribute] = ''
                output.user_identity_addition_reminder(len(list_of_end_users))
    for user in list_of_end_users:
        user.create_tasks(NumOfTaskPerUser, blockchainFunction, list_of_end_users)
        user.send_tasks(fogNodes)
        print("End_user " + str(user.addressParent) + "." + str(user.addressSelf) + " had sent its tasks to the fog layer")


def initiate_miners():
    the_miners_list = []

    if blockchainPlacement == 1:
        for i in range(NumOfFogNodes):
            the_miners_list.append(miner.Miner(i + 1, trans_delay, gossip_activated))
    if blockchainPlacement == 2:
        for i in range(NumOfMiners):
            the_miners_list.append(miner.Miner(i + 1, trans_delay, gossip_activated))
    for entity in the_miners_list:
        modification.write_file("temporary/" + entity.address + "_local_chain.json", {})
        miner_wallets_log_py = modification.read_file("temporary/miner_wallets_log.json")
        miner_wallets_log_py[str(entity.address)] = data['miners_initial_wallet_value']
        modification.rewrite_file("temporary/miner_wallets_log.json", miner_wallets_log_py)
    print('Miners have been initiated..')
    connect_miners(the_miners_list)
    output.miners_are_up()
    return the_miners_list


def define_trans_delay(layer):
    transmission_delay = 0
    if layer == 1:
        transmission_delay = delay_between_fog_nodes
    if layer == 2:
        transmission_delay = delay_between_end_users
    return transmission_delay


def connect_miners(miners_list):
    print("Miners will be connected in a P2P fashion now. Hold on...")
    bridges = set()
    all_components = create_components(miners_list)
    for comp in all_components:
        bridge = random.choice(tuple(comp))
        bridges.add(bridge)
    bridging(bridges, miners_list)


def bridging(bridges, miners_list):
    while len(bridges) != 1:
        bridge = random.choice(tuple(bridges))
        other_bridge = random.choice(tuple(bridges))
        same_bridge = True
        while same_bridge:
            other_bridge = random.choice(tuple(bridges))
            if other_bridge != bridge:
                same_bridge = False
        for entity in miners_list:
            if entity.address == bridge:
                entity.neighbours.add(other_bridge)
            if entity.address == other_bridge:
                entity.neighbours.add(bridge)
        bridges.remove(bridge)


def create_components(miners_list):
    all_components = set()
    for entity in miners_list:
        component = set()
        while len(entity.neighbours) < number_of_miner_neighbours:
            neighbour = random.choice(miners_list).address
            if neighbour != entity.address:
                entity.neighbours.add(neighbour)
                component.add(neighbour)
                for entity_2 in miners_list:
                    if entity_2.address == neighbour:
                        entity_2.neighbours.add(entity.address)
                        component.add(entity.address)
                        break
        if component:
            all_components.add(tuple(component))
    return all_components


def give_miners_authorization(the_miners_list, the_type_of_consensus):
    if the_type_of_consensus == 1:
        wanted, float_portion = output.AI_assisted_mining_wanted()
        if wanted:
            num_of_miners_requested_to_use_AI = ceil(float_portion * len(the_miners_list))
            num_of_miners_instructed_to_use_AI = 0
            while num_of_miners_instructed_to_use_AI < num_of_miners_requested_to_use_AI:
                random_miner = random.choice(the_miners_list)
                if not random_miner.adversary:
                    random_miner.adversary = True
                    num_of_miners_instructed_to_use_AI += 1
            print(str(num_of_miners_instructed_to_use_AI) + ' miners were successfully instructed to use AI.')
        return wanted
    if the_type_of_consensus == 3:
        # automated approach:
        if Automatic_PoA_miners_authorization:
            for i in range(len(the_miners_list)):
                the_miners_list[i].isAuthorized = True
                list_of_authorized_miners.append(the_miners_list[i])
        else:
            # user input approach:
            output.authorization_trigger(blockchainPlacement, NumOfFogNodes, NumOfMiners)
            while True:
                authorized_miner = input()
                if authorized_miner == "done":
                    break
                else:
                    for node in the_miners_list:
                        if node.address == "Miner_" + authorized_miner:
                            node.isAuthorized = True
                            list_of_authorized_miners.append(node)
    return None


def initiate_genesis_block(AI_wanted,):
    genesis_transactions = ["genesis_block"]
    for i in range(len(miner_list)):
        genesis_transactions.append(miner_list[i].address)
        
        genesis_block = new_consensus_module.generate_new_block(genesis_transactions, 'The Network', 0, type_of_consensus, AI_wanted, False)
    output.block_info(genesis_block, type_of_consensus)
    for elem in miner_list:
        elem.receive_new_block(genesis_block, type_of_consensus, miner_list, blockchainFunction, expected_chain_length)
    output.genesis_block_generation()


def send_tasks_to_BC():
    global user_informed
    for node in fogNodes:
        node.send_tasks_to_BC(user_informed)
        if not user_informed:
            user_informed = True


def store_fog_data():
    for node in fogNodes:
        log = open('temporary/Fog_node_'+str(node.address)+'.txt', 'w')
        log.write(str(node.local_storage))


def inform_miners_of_users_wallets():
    if blockchainFunction == 3:
        user_wallets = {}
        for user in list_of_end_users:
            wallet_info = {'parent': user.addressParent,
                           'self': user.addressSelf,
                           'wallet_value': user.wallet}
            user_wallets[str(user.addressParent) + '.' + str(user.addressSelf)] = wallet_info
        for i in range(len(miner_list)):
            modification.rewrite_file(str("temporary/" + miner_list[i].address + "_users_wallets.json"), user_wallets)

""" def select_leader(list_of_miners):
    selected_miner = random.choice(list_of_miners)
    selected_miner.leader = True
    for entity in list_of_miners:
        entity.leader = selected_miner.address 
        entity.number_of_miners = len(list_of_miners)#
        entity.number_of_tolerated_adversaries = entity.number_of_miners /2  
        
        
    return list_of_miners """
def isleader_todo(list_of_miners):
        selected_of_miner=random.choice(list_of_miners)
        selected_of_miner.leader =True
        for entity in list_of_miners:
            leader_index = entity.view_number % len(list_of_miners)
            entity.leader = list_of_miners[leader_index]
        if (selected_of_miner.address == entity.leader) and (entity.status == None):
            print("\t \t \tcorrect")
        return list_of_miners


if __name__ == '__main__':
    user_input()
    initiate_network()
    miner_list = initiate_miners()
    type_of_consensus = new_consensus_module.choose_consensus()
    if type_of_consensus !=6:
        trans_delay = define_trans_delay(blockchainPlacement)
        AI_assisted_mining_wanted = give_miners_authorization(miner_list, type_of_consensus)
        inform_miners_of_users_wallets()
        blockchain.stake(miner_list, type_of_consensus)
        initiate_genesis_block(AI_assisted_mining_wanted)
        send_tasks_to_BC()
        time_start = time.time()
        if blockchainFunction == 2:
            expected_chain_length = ceil((num_of_users_per_fog_node * NumOfTaskPerUser * NumOfFogNodes))
        new_consensus_module.miners_trigger(miner_list, type_of_consensus, expected_chain_length, Parallel_PoW_mining,
                                            numOfTXperBlock, blockchainFunction, poet_block_time, Asymmetric_key_length,
                                            number_of_DPoS_delegates, AI_assisted_mining_wanted)

        blockchain.award_winning_miners(len(miner_list), miner_list)
        blockchain.fork_analysis(miner_list)
        output.finish()
        store_fog_data()
        elapsed_time = time.time() - time_start
        print("elapsed time = " + str(elapsed_time) + " seconds")
    else:
        miner_list=isleader_todo(miner_list)
        print("print miners init",miner_list)
        AI_assisted_mining_wanted=give_miners_authorization(miner_list,type_of_consensus)
        initiate_genesis_block(miner_list)
        send_tasks_to_BC() 
        new_consensus_module.miners_trigger(miner_list, type_of_consensus, expected_chain_length, Parallel_PoW_mining,
                                            numOfTXperBlock, blockchainFunction, poet_block_time, Asymmetric_key_length,
                                            number_of_DPoS_delegates,AI_assisted_mining_wanted)
        """ while True:
            try:
                time.sleep(1)
                if isleader_todo():
                    miner.print_debug("Leader to do (PPRE)")
                    msg = miner.gen_preprepare_msg()
                    miner.print_debug("Broadcast --(PPRE)-->> ")
                    Process(miner_list, "PPRE", msg)
                else:
                    (src_id, msgtype, msgdata) = Process(target=miner.receive_new_block())
                    next_action = miner.handler[msgtype](src_id, msgdata)
                    if next_action == "PREP":
                        msg = miner.gen_prepare_msg()
                        miner.print_debug("Broadcast --(PREP)-->> ")
                        Process(miner_list, "PREP", msg)
                    elif next_action == "COMM":
                        msg = miner.gen_commit_msg()
                        miner.print_debug("Broadcast --(COMM)-->>")
                        Process(miner_list, "COMM", msg)
                    elif next_action == "REPL":
                        (requester, msg) = miner.gen_reply_msg()
                        miner.print_debug("Send --(REPL)--> " + str(requester))
                        Process(requester, "REPL", msg)
                        miner.round_finish()
            except KeyboardInterrupt:
                Process.close()
                
                break
            except:
                continue   """
      
        

