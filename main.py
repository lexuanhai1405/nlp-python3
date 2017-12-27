import nltk
from nltk import load_parser
from nltk.tree import Tree
import inspect
import re
import os
import glob
from nltk.sem import cooper_storage as cs

read_expr = nltk.sem.Expression.fromstring
cp = load_parser('grammar.fcfg')
#nltk.data.show_cfg('grammar.fcfg')

# Clean output folder
files = glob.glob('output/*')
for f in files: 
	os.remove(f)

output = open('output/output_a.txt', 'a')
output.write('Not ouput!!!')

# Read input
questions = open('input.txt', 'r').readlines()

# Begin loop throught th questions
for question in questions:
	print('Q: ' + question.strip())
	# Retrieve the tokens
	print('\tSpliting tokens...')
	question = question.strip('?\r\t\n\f ')
	prop = question.replace('what time does', '') \
					.replace('when does', '') \
					.replace('which', '')
	tokens = [question.replace(prop, '').strip()]
	prop2 = prop.split('Hồ Chí Minh')
	if len(prop2) == 2:
		tokens = tokens + prop2[0].split() + ['Hồ Chí Minh'] + prop2[1].split()
	else:
		tokens = tokens + prop.split()
	#print(tokens)


	# Parse syntax tree
	print('\tParsing the syntax tree...')
	tree = cp.parse_all(tokens)[0]
	tree_str = tree.__str__();
	for e in re.findall('\[[^\]]*\]', tree_str):
		tree_str = tree_str.replace(e,'')

	output = open('output/output_b.txt', 'a')
	output.write(tree_str)
	output.write('\n\n====================================\n\n')
	#print(tree_str)

	print('\tGenerating the logical form...')
	wh_query = tree[0].leaves()[0]
	if wh_query == 'which':
		s_sem = r'\f.?wh'
	elif wh_query == 'when does' or wh_query == 'what time does':
		s_sem = r'\t.?wh'

	wh_query_sem = tree[0].label()['SEM'].__str__()
	flight_np_sem = tree[1].label()['SEM'].__str__()
	flight_vp_sem = tree[2].label()['SEM'].__str__()

	wh_query_sem = read_expr(wh_query_sem + '({}, {})' \
		.format(flight_np_sem, flight_vp_sem)).simplify().__str__()
	s_sem = s_sem.replace('?wh', wh_query_sem)
	s_sem_o = read_expr(s_sem + '({})'.format(s_sem[1])).simplify().__str__()
	s_sem_o = s_sem_o.replace('WH_QUERY', 'WH_QUERY {}: '.format(s_sem[1])) \
						.replace('\\f.', '')

	output = open('output/output_c.txt', 'a')
	output.write(s_sem_o)
	output.write('\n\n====================================\n\n')
	#print(s_sem)

	print('\tGenerating the procedural semantic...')
	if s_sem[1] == 'f':
		x = '?f'
	elif s_sem[1] == 't':
		if 'ARRIVE' in flight_vp_sem:
			x = '?at'
		elif 'LEAVE' in flight_vp_sem:
			x = '?dt'
		else:
			raise ValueError('Failed to verb token.')
	else:
		raise ValueError('Failed to variable character.')

	# Rx -> (FLIGHT ?f)
	#flight_cnp_sem = next(x for x in tree[1][:] if 'FLIGHT-CNP' in x.__str__()).label()['SEM']
	if 'FLIGHT(f)' in flight_np_sem: 
		Rx = '(FLIGHT ?f)'
	else:
		flight_name = '' # No this case
		Rx = '(FLIGHT ' + flight_name + ')'

	#Px -> (ATIME ?f ?ac ?at)
	#Qx -> (DTIME ?f ?dc ?dt)
	try:
		s = next(x for x in flight_np_sem.split('&') if 'DEST' in x)
		name = re.search('NAME\([^\)]+\)', s).group()[5:-1]
		if 'NAME' in s:
			a_city_name = name
			a_time_mod = ''
		else:
			a_city_name = ''
			a_time_mod = name
	except Exception as e:
		a_time_mod = ''
		a_city_name = ''

	if 'ARRIVE' in flight_vp_sem:
		Qx = '(DTIME {} {} {})'.format('?f', '?dc', '?dt')
		if 'NAME' in flight_vp_sem:
			a_time_mod = re.search('NAME\([^\)]+\)', flight_vp_sem).group()[5:-1]
	elif 'NAME' in flight_vp_sem:
		name = re.search('NAME\([^\)]+\)', flight_vp_sem).group()[5:-1]
		Qx = '(DTIME {} {} {})'.format('?f', '?dc', name)
	else: 
		Qx = '(DTIME {} {} {})'.format('?f', '?dc', '?dt')


	if a_city_name == '': a_city_name = '?ac'
	if a_time_mod == '': a_time_mod = '?at'
	Px = '(ATIME {} {} {})'.format('?f', a_city_name, a_time_mod)

	proceduralSem = 'PRINT-ALL {} {} {} {}'.format(x, Rx, Px, Qx)
	
	output = open('output/output_d.txt', 'a')
	output.write(proceduralSem)
	output.write('\n\n====================================\n\n')
	#print(proceduralSem)


	print('\tFinding info from database...')
	s = '[^\s]+'
	pattern = '{} {} {}'.format(Rx, Px, Qx) \
							.replace('(', '\(') \
							.replace(')', '\)') \
							.replace('?f', s) \
							.replace('?ac', s) \
							.replace('?at', s) \
							.replace('?dc', s) \
							.replace('?dt', s)
	db = open('db', 'r')
	db = db.readlines()
	result = []
	for rec in db:
		sch = re.search(pattern, rec)
		if not sch is None:
			result.append(sch.group())

	output = open('output/output_e.txt', 'a')
	if result == None or len(result) <= 0:
		output.write('None\n')
	for r in result:
		if x == '?f': 
			rr = re.search('FLIGHT [^\)]+', r).group().split()[1]
		elif x == '?ac':
			rr = re.search('ATIME [^\)]+', r).group().split()[2]
		elif x == '?at':
			rr = re.search('ATIME [^\)]+', r).group().split()[3]
		elif x == '?dc':
			rr = re.search('DTIME [^\)]+', r).group().split()[2]
		elif x == '?dt':
			rr = re.search('DTIME [^\)]+', r).group().split()[3]
		output.write(rr + '\n')
		#print(rr)
	output.write('\n====================================\n\n')

	print('\tCompleted.\n')

# End Loop
print('--- Completed all. Outputs store in the "output" folder.---')