#!/usr/bin/env python

import radical.pilot as rp


if __name__ == "__main__":

	session = rp.Session()

	try:

		pmgr = rp.PilotManager(session=session)
		pdesc = list()
		
		pd_init = {
			'resource'			: 'xsede.stampede'
		,	'cores'				: 1024
		,	'runtime'			: 90 
		,	'project'			: 'TG-MCB090174'
		,	'queue'				: 'normal'
		}

		pdesc.append(rp.ComputePilotDescription(pd_init))
		pilots = pmgr.submit_pilots(pdesc)
		umgr = rp.UnitManager(session=session)
		umgr.add_pilots(pilots)

		cuds = list()

		for i in range(1000, 2024):
			cud = rp.ComputeUnitDescription()
			cud.executable = '/bin/cp'
			cud.arguments = ['-v', 'input_data_%03d.txt' % i, 'output_data_%03d.txt' % i]
			cud.input_staging = {
				'source'			: 'input_data_%03d.txt' % i
			,	'target'			: 'input_data_%03d.txt' % i
			,	'action'			: rp.TRANSFER
			}
			cud.output_staging = {
				'source'			: 'output_data_%03d.txt' % i
			,	'target'			: 'output_data_%03d.txt' % i
			,	'action'			: rp.TRANSFER
			}
			
			cuds.append(cud)

		umgr.submit_units(cuds)
		umgr.wait_units()

	except Exception as e:
		print 'Caught Exception: %s\n' % e
		raise
	
	except (KeyboardInterrupt, SystemExit) as e:
		print 'Exit Requested %s\n' %e
		raise
	
	finally:
		session.close()
