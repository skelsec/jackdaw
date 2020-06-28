import requests

CRACKED_ENDPOINT = '/credentials/{ad_id}/cracked'
PWSHARE_ENDPOINT = '/credentials/{ad_id}/pwsharing'
STATS_ENDPOINT = '/credentials/{ad_id}/stats'

PWSHARE_KEYS = ['pw_sharing_cracked', 'pw_sharing_notcracked', 'pw_sharing_total']

def build_report(url_base, ad_id, output_file):
	d = {
		'ad_id' : str(ad_id)
	}
	with open(output_file+ '_cracked.csv', 'w', newline = '') as f:
		r = requests.get(url_base + CRACKED_ENDPOINT.format(**d))
		if r.status_code != 200:
			raise Exception('Unexpected status code %s' % r.status_code)
		for entry in r.json():
			f.write('\t'.join(entry) + '\r\n')

	with open(output_file+ '_pwshare_stats.csv', 'w', newline = '') as f:
		with open(output_file+ '_pwshare.csv', 'w', newline = '') as o:
			r = requests.get(url_base + PWSHARE_ENDPOINT.format(**d))
			if r.status_code != 200:
				raise Exception('Unexpected status code %s' % r.status_code)
			jd = r.json()
			f.write('pw_sharing_cracked')
			f.write('\t'.join(PWSHARE_KEYS) + '\r\n')
			t = []
			for key in PWSHARE_KEYS:
				t.append(str(jd[key]))
			f.write('\t'.join(t))
			for entry_key in jd['pwsharing_users']:
				o.write('\t'.join(jd['pwsharing_users'][entry_key]) + '\r\n')

	with open(output_file+ '_stats.csv', 'w', newline = '') as f:
		r = requests.get(url_base + STATS_ENDPOINT.format(**d))
		if r.status_code != 200:
			raise Exception('Unexpected status code %s' % r.status_code)
		keys = []
		jd = r.json()
		for entry in jd:
			keys.append(entry)
		values = []
		for key in keys:
			values.append(str(jd[key]))
		
		f.write('\t'.join(keys) + '\r\n')
		f.write('\t'.join(values) + '\r\n')


def main():
	import argparse
	parser = argparse.ArgumentParser(description='Gather gather gather')
	parser.add_argument('ad_id', type=int, help='AD ID for which the report will be generated')
	parser.add_argument('-o','--outfile', default='report.csv', help='Base file name for the report -csv format-')
	parser.add_argument('-u', '--url', default = 'http://127.0.0.1:5000',  help='base URL of jackdaw API')
	args = parser.parse_args()

	build_report(args.url, args.ad_id, args.outfile)

if __name__ == '__main__':
	main()
