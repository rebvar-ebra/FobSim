#upon receiving a block: when the miner is false /randomly choose a leader/ then function build block
#1. verify it in terms of the application 
# we will use the function=> validate_transactions(self, list_of_new_transactions, miner_role)

#2. preprepare step: broadcast the valid block to all miners(process:block)
#3. according to n, miners initiate a database for confirmations()
#3. all miners verify it again for themselves

#4. prepare step: each miner broadcast the valid block 
#5. by the end of this step, all miners should know what is the exact number of nodes who would accept this block(append in to doctinory)
#6. check if number of confirmations >= ???? majority 2/3(optional condition)

#7. each miner adds the block to its local ledger (with flag" uncommited")
#8. miners initiate a database for commits
#9. broadcast a commit acknowledgement of the block
#10. repeat step 6 for the commits
#11. each miner changes the status of the block to "commited" if the condition is fulfilled.

#go to step 1 

