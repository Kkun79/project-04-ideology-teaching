import json
import copy

path = 'C:\\Users\\1\\Desktop\\workspace\\思政教学程序\\data\\exhibits.json'
data = json.load(open(path, encoding='utf-8'))

new_data = []
site_map = {}  # province_name -> list of site entries

for item in data:
    item = dict(item)
    title = item['title']
    
    if item['id'] in ['ex035', 'ex036', 'ex037', 'ex038']:
        # Beijing specific sites
        item['type'] = 'site'
        item['province'] = '北京'
        site_map.setdefault('北京', []).append(item)
    elif item['id'] in ['ex039', 'ex040']:
        # Liaoning specific sites
        item['type'] = 'site'
        item['province'] = '辽宁'
        site_map.setdefault('辽宁', []).append(item)
    elif item['id'] == 'ex041':
        # Shaanxi specific site
        item['type'] = 'site'
        item['province'] = '陕西'
        site_map.setdefault('陕西', []).append(item)
    else:
        # Province overview
        item['type'] = 'province'
        # Extract province name (remove "省" suffix and region prefix)
        province_name = title.split('——')[0].split('—')[0].strip()
        # Handle special cases
        name_map = {
            '北京': '北京', '天津': '天津', '河北': '河北', '山西': '山西',
            '内蒙古': '内蒙古', '辽宁': '辽宁', '吉林': '吉林', '黑龙江': '黑龙江',
            '上海': '上海', '江苏': '江苏', '浙江': '浙江', '安徽': '安徽',
            '福建': '福建', '江西': '江西', '山东': '山东',
            '河南': '河南', '湖北': '湖北', '湖南': '湖南',
            '广东': '广东', '广西': '广西', '海南': '海南',
            '重庆': '重庆', '四川': '四川', '贵州': '贵州', '云南': '云南', '西藏': '西藏',
            '陕西': '陕西', '甘肃': '甘肃', '青海': '青海', '宁夏': '宁夏', '新疆': '新疆',
            '香港': '香港', '澳门': '澳门', '台湾': '台湾',
        }
        found = False
        for k, v in name_map.items():
            if title.startswith(k) or k in title:
                item['province'] = v
                found = True
                break
        if not found:
            item['province'] = province_name
        
        # Add existing site to its own province
        item['type'] = 'province'
        new_data.append(item)

# Add all site entries
for item in data:
    item = dict(item)
    if item['id'] in ['ex035', 'ex036', 'ex037', 'ex038', 'ex039', 'ex040', 'ex041']:
        pass  # already handled above
    else:
        # Check if this province has specific sites to show
        pass

# Actually, let me redo this more carefully
print("=== Original ===")
print(f"Total: {len(data)}")

final = []

# Process each original item
for item in data:
    entry = dict(item)
    title = entry['title']
    
    if entry['id'] in ['ex035', 'ex036', 'ex037', 'ex038']:
        entry['type'] = 'site'
        entry['province'] = '北京'
        final.append(entry)
    elif entry['id'] in ['ex039', 'ex040']:
        entry['type'] = 'site'
        entry['province'] = '辽宁'
        final.append(entry)
    elif entry['id'] == 'ex041':
        entry['type'] = 'site'
        entry['province'] = '陕西'
        final.append(entry)
    else:
        entry['type'] = 'province'
        final.append(entry)

# Print province overviews only
provinces = [x for x in final if x['type'] == 'province']
print(f"\n=== Province overviews: {len(provinces)} ===")
for p in provinces:
    print(f"  {p['id']}  {p['title']}")

sites = [x for x in final if x['type'] == 'site']
print(f"\n=== Specific sites: {len(sites)} ===")
for s in sites:
    print(f"  {s['id']}  {s['province']} - {s['title']}")

# Write
json.dump(final, open(path, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
print(f"\nWritten {len(final)} exhibits")
