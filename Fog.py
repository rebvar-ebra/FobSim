import random
import output
import mempool
import modification

data = modification.read_file("Sim_parameters.json")


class Fog:
    def __init__(self, address):
        self.address = address
        self.tasks = []
        self.list_of_connected_users = set()
        self.STOR_PLC = data["STOR_PLC(0=in the Fog,1=in the BC)"]
        self.local_storage = []

    def receive_tasks(self, tasks, sender):
        self.tasks.extend(tasks)
        self.list_of_connected_users.add(sender)

    def _put_tasks_to_mempool(self, tasks_to_add, blockchain_function):
        l2_enabled = data.get("Layer2_Rollup_Enabled", False)
        l2_batch_size = data.get("Layer2_Batch_Size", 100)
        
        if l2_enabled:
            for i in range(0, len(tasks_to_add), l2_batch_size):
                chunk = tasks_to_add[i:i + l2_batch_size]
                rollup_tx = ["ROLLUP", len(chunk), "simulated_zk_proof", blockchain_function]
                mempool.MemPool.put(rollup_tx)
        else:
            for task in tasks_to_add:
                mempool.MemPool.put(task)

    def send_tasks_to_BC(self, user_informed):
        temporary_task = random.choice(self.tasks)
        if not user_informed:
            output.inform_of_fog_procedure(temporary_task[-1], self.STOR_PLC)
            
        if temporary_task[-1] == 1:
            if self.STOR_PLC == 1:
                self._put_tasks_to_mempool(self.tasks, 1)
            else:
                self.local_storage.extend(self.tasks)
                
        if temporary_task[-1] == 2:
            tasks_to_mempool = []
            for task in self.tasks:
                for letter in task[-2]:
                    if letter in ['+', '-']:
                        result = eval(task[-2])
                        produced_transaction = [f'End-user address: {str(task[0])}.{str(task[1])}', f'Requested computational task: {str(task[2])}', f'Result: {str(result)}', f"Performed_by_fog_node_num: {str(self.address)}"]
                        self.local_storage.append(produced_transaction)
                        break
                    elif letter in ['/', '*']:
                        tasks_to_mempool.append(task)
                        break
            if tasks_to_mempool:
                self._put_tasks_to_mempool(tasks_to_mempool, 2)

        if temporary_task[-1] == 3:
            self._put_tasks_to_mempool(self.tasks, 3)
            
        if temporary_task[-1] == 4:
            self.local_storage.extend(self.tasks)
