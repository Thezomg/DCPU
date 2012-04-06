import re
import sys
import struct

registers = 'ABCXYZIJ'

label_exp = '(\w+)'

#Numerical expression or label

number_exp = (
	('0x([0-9A-Fa-f]+)', lambda n: (False, int(n, 16))), #Hex
	('0b([01]+)',        lambda n: (False, int(n, 2))),  #Binary
	('(\d+)',            lambda n: (False, int(n))),     #Decimal
	(label_exp,          lambda s: (True, s))            #Label
)

opcodes = {
	'SET': 1,
	'ADD': 2,
	'SUB': 3,
	'MUL': 4,
	'DIV': 5,
	'MOD': 6,
	'SHL': 7,
	'SHR': 8,
	'AND': 9,
	'BOR': 10,
	'XOR': 11,
	'IFE': 12,
	'IFN': 13,
	'IFG': 14,
	'IFB': 15}

extended_opcodes = {
	'JSR': 1}

operand_exp = []

#0x00-0x07: A, B, C, etc
#0x08-0x0F: [A], [B], [C], etc
#0x10-0x17: [next_word + register]     === 16bit!

for i, l in enumerate(registers):
	operand_exp.append((i,        '(%s)'      % l, None))
	operand_exp.append((i+8, '\[\s*(%s)\s*\]' % l, None))
	for nexp, h in number_exp:
		operand_exp.append((i+16, '\[\s*%s\s*\+\s*(%s)\s*\]' % (nexp, l), h))

#0x18-0x1d

operand_exp += (
	(0x18, '(POP)', None),
	(0x19, '(PEEK)', None),
	(0x1a, '(PUSH)', None),
	(0x1b, '(SP)', None),
	(0x1c, '(PC)', None),
	(0x1d, '(O)', None))

#0x1e     : [next_word]                === 16bit
#0x1f     : next_word                  === 16bit

for nexp, h in number_exp:
	operand_exp.append((0x1e, '\[\s*(%s)\s*\]' % nexp, h))
	operand_exp.append((0x1f, '(%s)' % nexp, h))

#0x20-0x3F: integer value (offset 0x20)
#Handled in 0x1f handler

class LabelRef:
	def __init__(self, name):
		self.name = name

class Label:
	def __init__(self, name):
		self.name = name

def dcpu_compile(input, output):
	labels = {}
	label_swap = []
	output_position = 0
	for line in input:
		realline = line
	
		#Strip comments
		line = line.split(';', 1)[0].strip()
	
		#Skip blank lines
		if not line:
			continue
	
		words = [0]      #Operation words (1 or more)
		operand_i = 0    #Operand counter
		operands = [0,0] #Operands
	
		#Check for a label!
		m = re.match('^\:'+label_exp, line)
		if m:
			labels[m.group(1)] = output_position/2
			line = line[m.end():].lstrip()
	
		#Match opcode
		opcode_name = line[:3]
		if opcode_name in opcodes:
			opcode = opcodes[opcode_name]
		elif opcode_name in extended_opcodes:
			opcode = 0
			operands[0] = extended_opcodes[opcode_name]
			operand_i = 1
		else:
			print "Unknown opcode on line %d" % (i+1)
			sys.exit(1)
	
		line = line[3:].lstrip()

		#Match operands
		while operand_i < 2:
			matched = False
			for ov, oexp, oh in operand_exp:
				m = re.match('^'+oexp+'[, ]*(.*)', line)
				if m:
					matched = True
					groups = list(m.groups())
				
					line = groups.pop(-1)
					operands[operand_i] = ov
				
					#Numerical expressions require processing
				
					if len(groups)>1:
						is_label, data = oh(groups[0]) #Parse the numerical value
						if is_label:
							label_swap.append((output_position + len(words) + 1, data))
							data = 0
						if ov in range(0x10, 0x18):
							words.append(data)
						elif ov == 0x1e:
							words.append(data)
						elif ov == 0x1f: #Pure numerical value
							#If it fits in 5 bits, pack it into the operand
							if data < 32 and not is_label:
								operands[operand_i] = 0x20 + data
							#Otherwise write another word
							else:
								words.append(data)
					break
			if not matched:
				print "Couldn't parse operand on line %d:" % (i+1)
				print line
				sys.exit(1)
			operand_i += 1
	
		line = line.strip()
		if line != '':
			print "Extraneous data on line %d: " % (i+1)
			print line
			sys.exit(1)
	
		#Make the first word
		words[0] = (operands[1] & 0x3F) << 10 | (operands[0] & 0x3F) << 4 | opcode

		#print ' '.join([('%04x' % words[i] if i < len(words) else '    ') for i in range(3)]) + ' | ' + realline.strip()

		#Write data!
		for w in words:
			output.write(chr(w   >> 8))
			output.write(chr(w & 0xFF))
		
		
		output_position += len(words)*2

		
	#Hotswap labels in
	for position, label in label_swap:
		output.seek(0)
		output.seek(position)
		label_pos = labels[label]
		output.write(chr(label_pos   >> 8))
		output.write(chr(label_pos & 0xFF))

if __name__ == '__main__':
	if len(sys.argv) != 3:
		print "Usage: python assemble.py in.txt out.bin"
	else:
		input = open(sys.argv[1], 'r')
		output = open(sys.argv[2], 'wb')
		dcpu_compile(input, output)
		input.close()
		output.close()
