import zipfile

for name in ['single_room.zip', 'single_scan_floor_only.zip', 'single_scan_with_ceiling.zip']:
    with zipfile.ZipFile(name, 'r') as z:
        print('=== ' + name + ' ===')
        nl = z.namelist()
        print('Total entries:', len(nl))
        top_levels = set(f.split('/')[0] for f in nl)
        print('Top level:', top_levels)
        subdirs = set('/'.join(f.split('/')[:2]) for f in nl if '/' in f)
        print('Subdirs sample:', sorted(list(subdirs))[:15])
        non_png = [f for f in nl if not f.endswith('.png') and not f.endswith('/')]
        print('Non-png files count:', len(non_png))
        print('Non-png files:', non_png[:30])
