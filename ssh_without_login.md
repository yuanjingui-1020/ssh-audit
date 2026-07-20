在 Windows 上配置 SSH 免密登录，核心逻辑就是**在本地生成一对密钥（公钥和私钥），然后把公钥扔给目标服务器**。

Windows 10 和 11 已经内置了 OpenSSH 客户端，可以直接在终端（PowerShell 或 CMD）中完成配置。以下是具体操作步骤：

1. **生成 SSH 密钥:** 如果你之前已经生成过密钥，可以跳过这一步.
1. 按下 `Win + R`，输入 `powershell` 并回车，打开 PowerShell。
2. 输入以下命令生成密钥（推荐使用更安全高效的 ed25519 算法）：

```bash
ssh-keygen -t ed25519 -C "your_email@example.com"

```

*(如果你连接的老旧服务器不支持 ed25519，请换成 `ssh-keygen -t rsa -b 4096`)*
3. **一路回车即可**：

* 提示保存路径时，直接回车（默认保存在 `C:\Users\你的用户名\.ssh\` 下）。
* 提示输入 passphrase（密码短语）时，**直接回车留空**。如果这里设置了密码，以后每次连接还是会要求输入这个密码短语，就达不到“完全免密”的效果了。


2. **将公钥推送到目标服务器:**
Windows 默认没有 Linux 上的 `ssh-copy-id` 快捷命令，但我们可以用一条 PowerShell 命令组合来完成。

在 PowerShell 中，复制并运行以下命令（请把 `user@服务器IP` 替换成你实际的用户名和服务器地址）：

```powershell
Get-Content $env:USERPROFILE\.ssh\id_ed25519.pub | ssh user@服务器IP "mkdir -p ~/.ssh && touch ~/.ssh/authorized_keys && chmod 700 ~/.ssh && chmod 600 ~/.ssh/authorized_keys && cat >> ~/.ssh/authorized_keys"

```

*注意：运行这条命令时，会要求你输入最后一次目标服务器的登录密码。*

> **手动复制法（如果上面命令报错）：**
> 1. 在本地电脑用记事本打开 `C:\Users\你的用户名\.ssh\id_ed25519.pub`，复制里面的所有内容。
> 2. 登录到你的服务器，运行 `nano ~/.ssh/authorized_keys`。
> 3. 将刚刚复制的内容粘贴到新的一行，保存并退出（按 `Ctrl+O` 回车保存，`Ctrl+X` 退出）。
> 
> 


3. **测试免密登录:**
现在，你可以测试是否配置成功。在 PowerShell 中输入：

```bash
ssh user@服务器IP

```

如果直接进入了服务器的命令行界面，而没有要求你输入密码，就说明配置成功了！
