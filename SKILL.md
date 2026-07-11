---
name: ssh-audit
description: SSH 瀹¤鎶€鑳姐€傛墍鏈?SSH 杩滅▼鎿嶄綔閫氳繃 SSHAuditClient 鎵ц锛岃嚜鍔ㄨ褰?JSONL 瀹¤鏃ュ織锛屽唴缃?14 鏉￠珮鍗卞懡浠ゆ娴嬭鍒欙紝鏀寔鍛戒护鎵ц銆佷氦浜掑紡 Shell銆佷細璇濆洖鏀俱€傚瘑鐮?Windows DPAPI 鍔犲瘑瀛樺偍锛屾棩蹇楃浉瀵硅矾寰勫瓨鍌紝椤圭洰鍙暣浣撹縼绉汇€?---



# SSH 瀹¤鎶€鑳?
## 鐩殑

鏈妧鑳藉己鍒舵墍鏈?SSH 杩滅▼鎿嶄綔璧板璁￠€氶亾銆侫I 鎵ц浠讳綍 SSH 鍛戒护鏃讹紝**蹇呴』**浣跨敤鏈」鐩殑 CLI 宸ュ叿鎴?Python 搴擄紝绂佹瑁?paramiko / subprocess ssh / 鍏朵粬 SSH 搴撶洿杩炪€傛墍鏈夋搷浣滆嚜鍔ㄨ褰?JSONL 瀹¤鏃ュ織銆佽Е鍙戣鍒欐娴嬨€佹敮鎸佷簨鍚庡洖鏀俱€?
---

## 椤圭洰璺緞锛堢幆澧冨彉閲忚嚜鍔ㄥ彂鐜帮級

**鏈妧鑳戒笉纭紪鐮佷换浣曠粷瀵硅矾寰勩€?* 浣跨敤鍓嶉€氳繃鐜鍙橀噺 `AGENT_SSH_AUDIT_HOME` 瀹氫綅椤圭洰鏍圭洰褰曘€傚鏋滅幆澧冨彉閲忔湭璁剧疆锛屾寜浠ヤ笅浼樺厛绾ф煡鎵撅細

1. 鐜鍙橀噺 `AGENT_SSH_AUDIT_HOME`锛堝綋鍓嶈繘绋嬶級
2. Windows Machine 绾х幆澧冨彉閲?`AGENT_SSH_AUDIT_HOME`
3. 鍏滃簳锛歚storage.py` 鍩轰簬鑷韩鑴氭湰浣嶇疆鑷姩鎺ㄥ

**AI 棣栨浣跨敤鍓?*锛氬厛妫€鏌ョ幆澧冨彉閲忔槸鍚﹀凡璁剧疆锛?
```powershell
$env:AGENT_SSH_AUDIT_HOME
```

鑻ヤ负绌猴紝杩愯 `install.ps1` 瀹屾垚鍒濆鍖栥€?
---

## 宸ュ叿閫夋嫨鍐崇瓥鏍?
**Python 杩愯鏃?*锛氭湰鎶€鑳借嚜甯﹀祵鍏ュ紡 Python 3.11.8锛堜綅浜?`python\python.exe`锛夛紝鏃犻渶绯荤粺瀹夎 Python銆傛墍鏈夊懡浠や腑鐨?`python` 鍧囨寚 `python\python.exe`锛堢浉瀵逛簬 `$env:AGENT_SSH_AUDIT_HOME`锛夈€?
```
闇€瑕?SSH 鎿嶄綔
  鈹溾攢 鍗曟潯鍛戒护鎵ц
  鈹?  鈹斺攢 python\python.exe bin\agent-ssh-run.py user@host "鍛戒护" --password-base64 xxx
  鈹溾攢 澶氭潯鍛戒护椤哄簭鎵ц
  鈹?  鈹斺攢 python\python.exe bin\agent-ssh-run.py user@host --batch commands.txt --password-base64 xxx
  鈹溾攢 浜や簰寮?Shell
  鈹?  鈹斺攢 python\python.exe bin\agent-ssh-shell.py user@host --password-base64 xxx
  鈹溾攢 Python 鑴氭湰涓泦鎴?  鈹?  鈹斺攢 from agent_ssh_audit import SSHAuditClient
  鈹斺攢 鍥炴斁/鏌ョ湅鍘嗗彶
      鈹斺攢 python\python.exe bin\agent-ssh-replay.py
```

鎵€鏈夊懡浠ゆ墽琛屽墠鍏?cd 鍒?`$env:AGENT_SSH_AUDIT_HOME`銆?
---

## 瀵嗙爜鍑嵁澶勭悊

### 鍔犲瘑瀛樺偍锛圵indows DPAPI锛?
鍑嵁浣跨敤 **Windows DPAPI锛圖ata Protection API锛?* 鍔犲瘑瀛樺偍銆傝皟鐢?`CryptProtectData`/`CryptUnprotectData`锛屽姞瀵嗘暟鎹粦瀹氬埌褰撳墠鐢ㄦ埛鐧诲綍浼氳瘽銆傜壒鎬э細

- **瀵嗙爜涓嶈惤鐩樻槑鏂?*锛氬嵆浣?`credentials.txt` 娉勯湶锛岃劚绂诲綋鍓嶇敤鎴蜂細璇濇棤娉曡繕鍘熷瘑鐮?- **缁戝畾鐢ㄦ埛浼氳瘽**锛氬叾浠栫敤鎴枫€佸叾浠栫▼搴忋€佽法鏈哄櫒/璺ㄧ敤鎴峰鍒跺悗鍧囨棤娉曡В瀵?- **鏃犻渶绠＄悊瀵嗛挜**锛氭搷浣滅郴缁熻嚜鍔ㄥ鐞嗗瘑閽ユ淳鐢熴€佸瓨鍌ㄥ拰杞崲
- **鑷姩鍗囩骇**锛氳鍙栨棫鐗?Fernet AES / Base64 鍑嵁鏃惰嚜鍔ㄥ師鍦板崌绾т负 DPAPI

### 鍑嵁绠＄悊 CLI

鎵€鏈夊嚟鎹鐞嗛€氳繃 `agent-ssh-cred.py` 瀹屾垚锛?
```powershell
# 鍔犲瘑瀛樺偍瀵嗙爜锛堜氦浜掕緭鍏ワ紝涓嶅洖鏄撅級
python\python.exe bin\agent-ssh-cred.py store 192.168.1.100

# 鍔犲瘑瀛樺偍瀵嗙爜锛堝懡浠よ浼犲弬锛?python\python.exe bin\agent-ssh-cred.py store 192.168.1.100 "MyP@ssword"

# 瑙ｅ瘑鑾峰彇瀵嗙爜锛堣緭鍑?Base64锛屽彲鐩存帴鐢ㄤ簬 --password-base64锛?python\python.exe bin\agent-ssh-cred.py get 192.168.1.100

# 鍒楀嚭鎵€鏈夊嚟鎹?python\python.exe bin\agent-ssh-cred.py list

# 鍒犻櫎鍑嵁
python\python.exe bin\agent-ssh-cred.py delete 192.168.1.100

# 鍗囩骇鏃х増 Base64 鍑嵁涓?AES 鍔犲瘑
python\python.exe bin\agent-ssh-cred.py migrate
```

### AI 鑾峰彇娴佺▼锛堟瘡娆?SSH 鎿嶄綔蹇呴』鎵ц锛?
1. **灏濊瘯鑷姩璇诲彇**锛氫娇鐢?`python\python.exe bin\agent-ssh-cred.py get <IP>` 灏濊瘯瑙ｅ瘑鑾峰彇瀵嗙爜
2. **鍑嵁涓嶅瓨鍦ㄦ椂绱㈣**锛氳嫢杩斿洖閿欒锛屽悜鐢ㄦ埛璇㈤棶鐩爣涓绘満鐨?SSH 瀵嗙爜銆傚憡鐭ョ敤鎴凤細**涓绘満鍦板潃**銆?*鐧诲綍鐢ㄦ埛**
3. **璇㈤棶瀛樼暀**锛氳幏寰楀瘑鐮佸悗锛岃闂敤鎴枫€屾槸鍚﹀皢姝ゅ瘑鐮佸姞瀵嗗瓨鍌紝浠ヤ究鍚庣画鑷姩浣跨敤锛熴€?4. **鍔犲瘑瀛樺偍**锛氳嫢鐢ㄦ埛鍚屾剰锛屾墽琛?`python\python.exe bin\agent-ssh-cred.py store <IP> <瀵嗙爜>`
5. **绂佹琛屼负**锛氱姝㈠湪鑴氭湰/鍥炲/鏃ュ織涓槑鏂囧睍绀哄瘑鐮侊紱绂佹灏嗗瘑鐮佺‖缂栫爜鍒颁换浣曟枃浠讹紱绂佹浣跨敤 `--password 鏄庢枃瀵嗙爜`

### 闆嗘垚鍒?SSH 鍛戒护

```powershell
# 浠庡嚟鎹簱鑾峰彇瀵嗙爜骞舵墽琛?SSH 鍛戒护
$pwBase64 = python\python.exe bin\agent-ssh-cred.py get 192.168.1.100
if ($LASTEXITCODE -eq 0) {
    python\python.exe bin\agent-ssh-run.py appen@192.168.1.100 "df -h" --password-base64 $pwBase64
}
```

### 鎵嬪姩瑙ｅ瘑鏌ョ湅锛堣皟璇曠敤锛?
```powershell
# 瑙ｅ瘑骞惰緭鍑烘槑鏂囧瘑鐮?python\python.exe bin\agent-ssh-cred.py get-plain 192.168.1.100
```

> **娉ㄦ剰**锛歚get-plain` 浠呰皟璇曠敤锛孉I 涓嶅緱鍦ㄥ洖澶嶄腑灞曠ず鏄庢枃瀵嗙爜銆?
### 浠€涔堟槸 DPAPI 鍔犲瘑锛屼互鍙婂浣曡В瀵嗚幏鍙?
`agent-ssh-cred.py` 鍐呴儴閫氳繃 `ctypes` 鐩存帴璋冪敤 Windows `crypt32.dll` 鐨?`CryptProtectData` / `CryptUnprotectData`锛屾棤闇€棰濆渚濊禆銆?
**鍔犲瘑鍘熺悊**锛欴PAPI 鏄?Windows 鍐呯疆鐨勬暟鎹繚鎶ゆ満鍒躲€傚姞瀵嗗瘑閽ョ敱鐢ㄦ埛鐧诲綍瀵嗙爜娲剧敓骞朵繚瀛樺湪鎿嶄綔绯荤粺瀵嗛挜搴撲腑锛屽洜姝わ細
- 鍙湁鍔犲瘑鏃剁殑鍚屼竴 Windows 鐢ㄦ埛鍙互瑙ｅ瘑
- 鍗充娇鍦ㄥ悓涓€鍙版満鍣ㄤ笂锛屽叾浠栫敤鎴?绋嬪簭涔熸棤娉曡В瀵嗭紙鍖呮嫭绠＄悊鍛樿繍琛岀殑鍏朵粬杩涚▼锛?- Windows 瀵嗙爜閲嶇疆鍚庢棫鏁版嵁鑷姩澶辨晥锛堝畨鍏ㄨ涓猴紝涓嶆槸 bug锛?
**瀹夊叏瀵规瘮**锛?
| 濞佽儊鍦烘櫙 | 鏃ф柟妗?(Fernet) | 鏂版柟妗?(DPAPI) |
|---------|----------------|---------------|
| credentials.txt 琚獌鍙栧悗绂荤嚎鐮磋В | 鍙互闃插尽 | 鍙互闃插尽 |
| 鍚屾満鍏朵粬绋嬪簭璋冪敤 crypto 妯″潡瑙ｅ瘑 | **涓嶈兘闃插尽** | **鍙互闃插尽** |
| 鎹㈡満鍣?鎹㈢敤鎴?| 涓嶈兘瑙ｅ瘑 | 涓嶈兘瑙ｅ瘑 |
| 绠＄悊鍛樿繘绋?| 鍙互瑙ｅ瘑 | 鍙互瑙ｅ瘑 |

**濡備綍瑙ｅ瘑鑾峰彇鍑嵁**锛?```powershell
python\python.exe bin\agent-ssh-cred.py get 192.168.1.100
```
杈撳嚭鍗充负瀵嗙爜鐨?Base64 缂栫爜锛屽彲鐩存帴鐢ㄤ簬 `--password-base64`銆?
**鎹㈡満鍣ㄨ縼绉诲嚟鎹?*锛氶渶鍦ㄦ柊鏈哄櫒涓婇噸鏂版墽琛?`store` 鍛戒护瀛樺偍瀵嗙爜銆侱PAPI 鍔犲瘑鏁版嵁鏃犳硶璺ㄧ敤鎴?璺ㄦ満鍣ㄨВ瀵嗏€斺€旇繖鏄畨鍏ㄨ璁°€?
**Windows 瀵嗙爜閲嶇疆娉ㄦ剰浜嬮」**锛歐indows 瀵嗙爜琚鐞嗗憳寮哄埗閲嶇疆鍚庯紝璇ョ敤鎴疯处鎴蜂笅鐨?DPAPI 瀵嗛挜浼氳娓呴櫎锛屾棫鐨勫姞瀵嗗嚟鎹皢姘镐箙鏃犳硶瑙ｅ瘑銆傝繖鏄?DPAPI 鐨勫畨鍏ㄧ壒鎬с€傚缓璁瘑鐮侀噸缃悗閲嶆柊 `store` 鎵€鏈夊嚟鎹€?
**Python 浠ｇ爜涓洿鎺ヨВ瀵?*锛?```python
from agent_ssh_audit.crypto import decrypt_password, get_credential
from pathlib import Path

# 鏂瑰紡 1锛氫粠 credentials.txt 鎸?key 璇诲彇骞惰В瀵?pw = get_credential("192.168.1.100", Path("credentials.txt"))

# 鏂瑰紡 2锛氱洿鎺ヨВ瀵嗗瘑鏂囷紙鑷姩璇嗗埆 dpapi:/gAAAAAB/Base64 鏍煎紡锛?pw = decrypt_password("dpapi:AQAAAN...")
```

---

## CLI 浣跨敤瑙勮寖

```powershell
# 鍗曟潯鍛戒护
python\python.exe bin\agent-ssh-run.py <user>@<host> "<command>" --password-base64 <base64瀵嗙爜>

# 鎵归噺鍛戒护
python\python.exe bin\agent-ssh-run.py appen@192.168.1.100 --batch <commands.txt璺緞> --password-base64 $pwBase64

# 浜や簰寮?Shell
python\python.exe bin\agent-ssh-shell.py appen@192.168.1.100 --password-base64 $pwBase64

# 瓒呮椂鎺у埗锛堥粯璁よ繛鎺?30s锛屽懡浠?60s锛?python\python.exe bin\agent-ssh-run.py appen@192.168.1.100 "apt update" --password-base64 $pwBase64 --timeout 120
```

---

## 鍛戒护灞曠ず涓庤В閲娿€愰噸瑕併€?
姣忔 SSH 鍛戒护鎵ц**缁撴潫鍚?*锛孉I **蹇呴』**鍚戠敤鎴峰睍绀轰互涓嬪唴瀹癸細

### 1锔忊儯 灞曠ず鎵ц鐨勫懡浠?
灏嗗疄闄呮墽琛岀殑鍏ㄩ儴鍛戒护鍒楀嚭锛屾瘡琛屼竴鏉°€備娇鐢?`--show-commands`锛堥粯璁ゅ紑鍚級鏃讹紝`agent-ssh-run.py` 浼氳嚜鍔ㄥ湪 stderr 杈撳嚭鍛戒护淇℃伅锛孉I 闇€灏嗗叾鏍煎紡鍖栧悗鍛堢幇缁欑敤鎴枫€?
### 2锔忊儯 閫愭潯瑙ｉ噴鍛戒护浣滅敤

瀵?*姣忎竴鏉?*鍛戒护锛岀粰鍑鸿嚜鐒惰瑷€鐨勮缁嗚В閲婏紝渚嬪锛?
| 鎵ц鍛戒护 | AI 鐨勮В閲?|
|---------|----------|
| `df -h` | 鏌ョ湅鏈嶅姟鍣ㄧ鐩樺垎鍖轰娇鐢ㄦ儏鍐碉紝`-h` 鍙傛暟浠ヤ汉绫诲彲璇绘牸寮忔樉绀猴紙GB/TB锛?|
| `systemctl status nginx` | 妫€鏌?Nginx 鏈嶅姟鐨勮繍琛岀姸鎬侊紝`status` 鏄剧ず鏄惁 active銆佹渶杩戞棩蹇楃墖娈?|
| `uname -a` | 鏌ョ湅绯荤粺鍐呮牳鐗堟湰涓庢灦鏋勪俊鎭紝`-a` 琛ㄧず鏄剧ず鍏ㄩ儴绯荤粺淇℃伅 |
| `ls -la /data` | 鍒楀嚭 `/data` 鐩綍涓嬫墍鏈夋枃浠讹紙鍚殣钘忔枃浠讹級锛宍-l` 浠ラ暱鏍煎紡鏄剧ず鏉冮檺銆佸睘涓汇€佸ぇ灏?|

**瑙ｉ噴鏍囧噯锛?*
- 璇存竻妤氬懡浠ょ殑**鐩殑**锛堜负浠€涔堣窇杩欐潯锛岃В鍐充粈涔堥棶棰橈級
- 璇存竻妤?*鍏抽敭鍙傛暟**鐨勫惈涔夛紙`-h`銆乣-a`銆乣-l` 绛夛級
- 浠?*鑷劧璇█**琛ㄨ堪锛岄潪鎶€鏈敤鎴蜂篃鑳界湅鎳?- 濡傛灉鍛戒护鎵ц澶辫触锛岄澶栬В閲婂け璐ョ殑鍙兘鍘熷洜

### 3锔忊儯 鍛堢幇鎵ц缁撴灉

灞曠ず鍛戒护鐨?stdout/stderr 杈撳嚭锛岄檮涓婇€€鍑虹爜锛堝鏋滈潪 0 鍒欓渶鏍囨槑锛夈€?
### 杈撳嚭绀轰緥

```
鈻?姝ｅ湪鎺掓煡纾佺洏鍛婅锛?
鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€
馃搵 鍛戒护 1锛歞f -h
鈹?浣滅敤锛氭煡鐪嬪悇鍒嗗尯鐨勭鐩樼┖闂村崰鐢ㄦ儏鍐?鈹?      -h 琛ㄧず浠?GB/TB 鍙鏍煎紡鏄剧ず
鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€
鏂囦欢绯荤粺          瀹归噺  宸茬敤  鍙敤  宸茬敤%  鎸傝浇鐐?/dev/sda1        100G   65G   35G   65%   /

鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€
馃搵 鍛戒护 2锛歴ystemctl status nginx
鈹?浣滅敤锛氭鏌?Nginx 鏈嶅姟杩愯鐘舵€?鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€
鈼?nginx.service - loaded, active (running)
  ...
```

---

## 鍛戒护瀛︿範鏃ュ織锛堢嫭绔嬩簬瀹¤锛?
鏈妧鑳藉唴缃竴涓?*鐙珛**鐨勫懡浠ゅ涔犳棩蹇楁ā鍧?`cmd_learner.py`锛屼笌瀹¤绯荤粺瀹屽叏瑙ｈ€︼細

### 鍔熻兘

- **鍙繚瀛樻墽琛岃繃鐨勫懡浠よ**锛屼笉鍚璁¤鍒欏懡涓€佽緭鍑虹粨鏋滅瓑楂橀樁鏁版嵁
- **Markdown 鏍煎紡锛屾寜澶╁綊妗?*锛屾瘡鏂囦欢 `$AGENT_SSH_AUDIT_HOME/cmds_learn/YYYY-MM-DD.md`
- **绾拷鍔犲啓鍏?*锛屼笉鐮村潖宸叉湁鍐呭
- 閫傜敤浜庯細鍚庢湡缈婚槄澶嶄範銆佹暣鐞嗗父鐢ㄥ懡浠ゃ€佸涔犳柊鎶€宸?
### 鏃ュ織鏂囦欢缁撴瀯绀轰緥

```markdown
# SSH 鍛戒护瀛︿範鏃ュ織

## 2026-07-11

### 22:38:15 | root@192.168.1.100 | sid:20260711_223815_root_192_168_1_100_a1b2
> 妫€鏌ョ鐩樹娇鐢ㄧ巼
```bash
df -h
```

### 22:38:20 | root@192.168.1.100 | sid:20260711_223815_root_192_168_1_100_a1b2
```bash
uname -a
```
```

### 鏌ョ湅瀛︿範鏃ュ織

```powershell
# 鏌ョ湅浠婂ぉ鐨勫涔犺褰?Get-Content "$env:AGENT_SSH_AUDIT_HOME\cmds_learn\$(Get-Date -Format 'yyyy-MM-dd').md"

# 鏌ョ湅鎵€鏈夊巻鍙叉枃浠?Get-ChildItem "$env:AGENT_SSH_AUDIT_HOME\cmds_learn\" *.md | Sort-Object Name -Descending
```

瀛︿範鏃ュ織**鑷姩璁板綍**锛孉I 鍜岀敤鎴峰潎鏃犻渶鎵嬪姩瑙﹀彂銆傝妯″潡涓嶅奖鍝嶅璁＄郴缁熻繍琛岋紝鏄湰鎶€鑳界殑闄勫姞鍔熻兘銆?
---

## Python 搴撲娇鐢?
```python
import os, sys
sys.path.insert(0, os.environ["AGENT_SSH_AUDIT_HOME"])
from agent_ssh_audit import SSHAuditClient

with SSHAuditClient(
    host="192.168.1.100", user="appen", password="appen",
    extra_audit_meta={"task": "鎺掓煡纾佺洏鍛婅", "ticket": "INC-12345"},
) as c:
    r = c.run("df -h")              # 鍗曟潯
    for r in c.run_many([...]):     # 鎵归噺
        ...
    sh = c.shell(); sh.send(...)    # 浜や簰
```

---

## 瀹¤瑙勫垯涓庡憡璀﹀鐞?
### 鍐呯疆瑙勫垯锛?4 鏉★級

| 绾у埆 | 瑙勫垯鍚?| 瑙﹀彂鍦烘櫙 |
|------|--------|---------|
| critical | `rm_rf_root` | `rm -rf /` |
| critical | `rm_rf_home` | `rm -rf ~`銆乣rm -rf $HOME` |
| warn | `rm_rf_absolute` | `rm -rf` 鍚庤窡缁濆璺緞 |
| critical | `dd_destructive` | `dd of=/dev/sd*` 绛夌鐩樺啓鍏?|
| critical | `mkfs` | `mkfs /dev/...` |
| critical | `chmod_recursive_root` | `chmod 777 /` |
| critical | `chown_recursive_root` | `chown ... /` |
| critical | `pipe_to_shell` | `curl url \| bash` |
| warn | `system_reboot` | `reboot`銆乣shutdown`銆乣halt` |
| critical | `disable_sshd` | `systemctl stop ssh` |
| warn | `firewall_flush` | `iptables -F` |
| warn | `passwd_change` / `user_mgmt` | `passwd`銆乣useradd`銆乣userdel` |
| critical | `edit_passwd_files` | 缂栬緫 `/etc/passwd`銆乣/etc/shadow`銆乣/etc/sudoers`銆乣/etc/ssh/sshd_config` |
| warn | `history_clear` | `history -c`銆佸垹闄?`.bash_history` |

### 鍛婅澶勭悊

- **warn 绾у埆**锛氬懡浠ゅ凡鎵ц銆傚洖澶嶄腑鍛婄煡鐢ㄦ埛銆岃鍛戒护鍛戒腑浜?XX 瀹¤瑙勫垯銆嶃€?- **critical 绾у埆**锛氬懡浠ゅ凡鎵ц涓旇褰曘€?*蹇呴』**鍦ㄥ洖澶嶄腑鏄庣‘鍛婄煡鐢ㄦ埛鍛戒腑鐨勮鍒欏悕鍜屽尮閰嶅唴瀹癸紝涓嶅彲闈欓粯蹇界暐銆?
### 瀹夊叏鍓嶇紑鐧藉悕鍗?
浠ヤ笅鍛戒护鍓嶇紑涓嶈Е鍙戝憡璀︼紙璁板綍浠嶅啓鍏ワ級锛?
```
ls, ll, cat, less, head, tail, grep, find, pwd, echo, printf,
uname, whoami, id, hostname, date, uptime, df, du, ps, top, env,
printenv, which, whereis, type, git status/log/diff/show/branch,
docker ps/images/logs/inspect, kubectl get/describe/logs,
systemctl status/list
```

---

## 鍥炴斁涓庢棩蹇?
鏃ュ織鑷姩鍐欏叆 `$env:AGENT_SSH_AUDIT_HOME\logs\sessions\YYYY-MM-DD\{session_id}.jsonl`銆?
```powershell
python\python.exe bin\agent-ssh-replay.py --list      # 鎵€鏈?session
python\python.exe bin\agent-ssh-replay.py --latest    # 鏈€杩戜竴娆?python\python.exe bin\agent-ssh-replay.py <id>        # 鎸囧畾 session
python\python.exe bin\agent-ssh-replay.py <id> --json # 鍘熷 JSON 娴?```

浠诲姟瀹屾垚鍚庡繀椤绘姤鍛婏細鎵ц鍛戒护鍙婄粨鏋溿€佸懡涓殑瀹¤瑙勫垯锛堝鏈夛級銆乻ession_id 鍜屾棩蹇楄矾寰勩€?
**瀛︿範鏃ュ織**锛圡arkdown锛屾寜澶╁綊妗ｏ級涔熻嚜鍔ㄨ褰曞湪 `$env:AGENT_SSH_AUDIT_HOME\cmds_learn\`锛岀敤鎴峰彲闅忔椂缈婚槄澶嶄範锛堣瑙佷笂鏂广€屽懡浠ゅ涔犳棩蹇椼€嶈鏄庯級銆?
---

## 閿欒澶勭悊

| 鐜拌薄 | 鍘熷洜 | 澶勭悊 |
|------|------|------|
| `AuthenticationException` | 瀵嗙爜閿欒 | 鍚戠敤鎴风‘璁ゅ瘑鐮侊紝閲嶈瘯涓€娆?|
| `socket.timeout` | 缃戠粶涓嶉€?| 鎶ュ憡鐢ㄦ埛鐩爣涓嶅彲杈?|
| `SSHException` | 鍗忚閿欒 | 閲嶈瘯涓€娆★紝浠嶅け璐ュ垯鎶ュ憡 |
| 瀹¤鍛戒腑 critical | 楂樺嵄鍛戒护 | 鍛婄煡鐢ㄦ埛瑙勫垯鍛戒腑鎯呭喌 |

---

## 绂佹琛屼负

1. 绂佹 `import paramiko` 鐩存帴寤虹珛 SSH 杩炴帴
2. 绂佹 `subprocess.run(["ssh", ...])` 缁曡繃瀹¤
3. 绂佹浣跨敤鍏朵粬 SSH 搴擄紙ssh2銆乫abric 绛夛級
4. 绂佹鍦ㄨ剼鏈?鍥炲/鏃ュ織涓槑鏂囧睍绀哄瘑鐮?5. 绂佹浣跨敤鏃х増 Base64 鏄庢枃绛夋晥瀛樺偍瀵嗙爜锛堝繀椤昏蛋 DPAPI 鍔犲瘑锛?6. 绂佹 critical 瑙勫垯鍛戒腑鍚庨潤榛樺拷鐣?7. 绂佹纭紪鐮佷换浣曠粷瀵硅矾寰勶紝鎵€鏈夎矾寰勪粠 `AGENT_SSH_AUDIT_HOME` 鎺ㄥ

---

## 渚濊禆

- Python 3.10+
- `paramiko`锛坄pip install paramiko`锛?- `cryptography`锛坄pip install cryptography`锛夆€?鏃х増鍑嵁杩佺Щ鏃堕渶瑕侊紙鍙€夛紝鏃ュ父 DPAPI 鍔犺В瀵嗘棤闇€姝ゅ簱锛?*锛堝唴瀹圭敱AI鐢熸垚锛屼粎渚涘弬鑰冿級*
