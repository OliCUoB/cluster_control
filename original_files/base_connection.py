from abc import ABCMeta, abstractmethod
import subprocess
import sys
import os
import time
class Connection(metaclass=ABCMeta):
	"""This is an abstract class that all connection classes inherit from."""
	def __init__(self, cluster_user_name, ssh_config_alias, path_to_key, forename_of_user, surname_of_user, user_email):
            """In order to initiate this class the user must have their ssh config file set up to have their cluster connection as an alias."""
		self.user_name = cluster_user_name
		self.ssh_config_alias = ssh_config_alias
		self.path_to_key = path_to_key
		self.forename_of_user = forename_of_user
		self.surename_of_user = surname_of_user
		self.user_email = user_email
		# add the ssh key so that if there's a password then the user can enter it now
		#ssh_add_cmd = "eval `ssh-agent -s`;ssh-add " + self.path_to_key
#		ssh_add_cmd = "ssh-add " + self.path_to_key
#		print("If you get an error just after this about not being able to add an ssh key (probably more like ssh-add doesn't exist or something) then it probably means that there is no ssh-agent running on the computer. To fix this in the linux terminal (on the central hub computer) run eval `ssh-agent -s` (they are backticks not single quotes) and then rerun this program/script etc.")
#		subprocess.check_output(ssh_add_cmd, shell=True)


	# instance methods
	def rsyncFile(self, source, destination, rsync_flags = "-aP"):
		"""UNDERSTAND RSYNC BEFORE YOU USE THIS FUNCTION!!! Uses rsync with specified flags to send a file to the cluster. source and destination only need the actual paths as the remote server will be done automatically."""
#		rsync_cmd = ["rsync", rsync_flags, source, self.ssh_config_alias + ":" + destination]
		rsync_cmd = "rsync " + rsync_flags + " " + source + " " + self.ssh_config_alias + ":" + destination
#		output = self.sendCommand([rsync_cmd])
		output = subprocess.call(rsync_cmd, shell=True)
#		exit_code = self.sendCommand(rsync_cmd)
		output_dict = {}
		output_dict['return_code'] = output

		return output_dict

	def convertKosAndNamesToFile(self, ko_code_dict, ko_code_file_path_and_name, ko_dir_name_file_path_and_name):
		"""Takes a python dict of gene codes and saves them in a specified path and file name."""
		# check that ko_code_dict has type "dict"
		if type(ko_code_dict) is not dict:
			raise TypeError("ko_code_dict must be a Python dict but here type(ko_code_dict)=%s" %(type(ko_code_dict)))

		# make sure paths exist and if not create them
		# take the file name off the end of both files
		# ko code path
		ko_code_path, ko_code_file = os.path.split(ko_code_file_path_and_name)
		# ko name path
		ko_name_path, ko_name_file = os.path.split(ko_dir_name_file_path_and_name)
		# if the paths don't exist then create them
		if os.path.isdir(ko_code_path) == False:
			os.makedirs(ko_code_path)

		if os.path.isdir(ko_name_path) == False:
			os.makedirs(ko_name_path)

		# save codes to the file
		ko_code_file = open(ko_code_file_path_and_name, 'wt', encoding='utf-8')
		ko_name_file = open(ko_dir_name_file_path_and_name, 'wt', encoding='utf-8')
		# currently the order of dictionaries in python is only preserved for version 3.6 and does not plan to make that a standard in the future and so for robustness I record the order that the codes and dirs are written to file
		order_of_keys = tuple(ko_code_dict.keys())
		for key in order_of_keys:
				ko_name_file.write(key + "\n")
				ko_code_file.write("'" + '\', \''.join(ko_code_dict[key]) + "'\n")

		ko_code_file.close()
		ko_name_file.close()

		return order_of_keys

	# static methods
	@staticmethod
	def checkSuccess(function, *args):
		"""This function takes a function that requires a remote connection and makes sure that the actual command completes."""

		# a list of the wait times (in seconds) between each loop should the connection keep failing
		# accumulative time:     15s 30s 45s  1m   6m  16m  30m   1hr   2hr   4hr    8hr   16hr   1day   2day   3day   4day   5day  6 day  7day
		wait_times = (3, 3, 3, 3, 3, 15, 15, 15, 300, 600, 840, 1800, 3600, 7200, 14400, 28800, 28800, 86400, 86400, 86400, 86400, 86400, 86400)

		# set flag to no successful connection attempt (successful exit code = 0)
		connection_success = 13
		for wait in wait_times:
			if connection_success != 0:
				try:
					output = function(*args)
					connection_success = output['return_code']
				except:
					connection_success = 13

			else:
				break

			if connection_success !=0:
				print('Connection failed. Waiting ' + str(wait) + ' seconds before attempting to reconnect.')
				time.sleep(wait)

		# depending on the result either output the data or stop the simulation
		if connection_success != 0:
			print("Could not get a successful connection after 7 days of trying and so now cancelling all the tasks!")
			sys.exit(13)
		else:
			return output

	def sendCommand(self, list_of_bash_commands):
		"""This takes a list of commands (in the subprocess module style shell=False) and sends them via subprocess.call(commands_as_a_list)"""
		sshProcess = subprocess.Popen(['ssh', '-T', self.ssh_config_alias], stdin=subprocess.PIPE, stdout = subprocess.PIPE, universal_newlines=True, bufsize=0)
		command = '\n'.join(list_of_bash_commands)
		print("command = ", command)
		out, err = sshProcess.communicate(command)
		return_code =  sshProcess.returncode
		sshProcess.stdin.close()
		output_dict = {}
		output_dict['return_code'] = return_code
		output_dict['stdout'] = out
		output_dict['stderr'] = err

#		connection_command = 'ssh ' + self.ssh_config_alias + ';exit;'
#		print(connection_command)
#		connection_command = ['ssh', '-i ' + self.path_to_key, self.user_name + '@' + self.ssh_config_alias, exit]
#		connection_command.append(bash_commands)
#		exit_code = subprocess.call(connection_command, shell=True)
		return output_dict

	@staticmethod
	def getOutput(commands_as_a_list):
		"""This takes a list of commands (in the subprocess module style shell=False) and sends them via subprocess.call(commands_as_a_list)"""
		# if the return code is zero then subprocess returns the output of the command or otherwise raises an exception. We want to keep trying if there is an exception and so use the following code.
		try:
			exitCode_output = [0, subprocess.check_output(commands_as_a_list)]
		except Exception:
			exitCode_output = [1, None]
		return exitCode_output

#	@staticmethod
#	def confirmConnection(pass_function???):
#		"""This takes a list of commands (in the subprocess module style shell=False) and sends them via subprocess.call(commands_as_a_list)"""
#		# if the return code is zero then subprocess returns the output of the command or otherwise raises an exception. We want to keep trying if there is an exception and so use the following code.
#		try:
#			exitCode_output = [0, subprocess.check_output(commands_as_a_list)]
#		except Exception:
#			exitCode_output = [1, None]
#		return exitCode_output

#	@staticmethod
#	def createSubmissionScript(list_of_lines, filename, file_permissions = "500"):
#		"""list_of_lines is a list where each entry is a new line in the script. It saves this in filename with permissions file_permissions."""
#		# open file
#		with open(filename, 'w') as outfile:
#			# write code to file
#			for line in list_of_lines:
#				outfile.write(line + "\n") 
#
#		# change file permisions
#		# create command
#		chmod_cmd = ["chmod", file_permissions, filename]
#		# send command
#		Connection.sendCommand(chmod_cmd)
#
#	# abstract methods
	@abstractmethod
	def checkQueue(self):
		pass

	@abstractmethod
	def checkDiskUsage(self):
		pass
