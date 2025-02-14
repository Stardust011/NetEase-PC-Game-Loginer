"""
此模块提供用于处理ssl证书。
"""

import datetime
import os
import platform
import shutil
import subprocess
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID

from Src.config import cfg
from Src.runtimeLog import debug, info, warning, error


def generate_ca_cert(ca_cert_file, ca_key_file):
    # 生成CA密钥
    ca_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

    # 创建CA证书
    subject = issuer = x509.Name(
        [
            x509.NameAttribute(NameOID.COUNTRY_NAME, "CN"),
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "Zhejiang"),
            x509.NameAttribute(NameOID.LOCALITY_NAME, "Hangzhou"),
            x509.NameAttribute(
                NameOID.ORGANIZATION_NAME, "Netease PC Game Loginer Project"
            ),
            x509.NameAttribute(NameOID.COMMON_NAME, "Netease PC Game Loginer Root CA"),
        ]
    )
    ca_cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(ca_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.datetime.now(datetime.UTC))
        .not_valid_after(
            datetime.datetime.now(datetime.UTC) + datetime.timedelta(days=3650)
        )
        .add_extension(x509.BasicConstraints(ca=True, path_length=None), critical=True)
        .add_extension(
            x509.KeyUsage(False, False, False, False, False, True, False, False, False),
            critical=True,
        )
        .add_extension(
            x509.SubjectKeyIdentifier.from_public_key(ca_key.public_key()),
            critical=False,
        )
        .add_extension(
            x509.AuthorityKeyIdentifier.from_issuer_public_key(ca_key.public_key()),
            critical=False,
        )
        .sign(ca_key, hashes.SHA256())
    )

    # 保存CA证书和密钥
    with open(ca_cert_file, "wb") as f:
        f.write(ca_cert.public_bytes(serialization.Encoding.PEM))
    with open(ca_key_file, "wb") as f:
        f.write(
            ca_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.NoEncryption(),
            )
        )
    info("CA证书与密钥已生成")


def generate_ca_cert_for_mitmproxy(mitmproxy_ca_cert_file, ca_cert_file, ca_key_file):
    # 加载文本CA证书和密钥直接写入mitmproxy-ca.pem
    # cat ca.key ca.crt > mitmproxy-ca.pem
    with open(ca_cert_file, "rb") as f:
        ca_cert = f.read()
    with open(ca_key_file, "rb") as f:
        ca_key = f.read()
    with open(mitmproxy_ca_cert_file, "wb") as f:
        f.write(ca_key)
        f.write(ca_cert)
    info("mitmproxy-ca证书已生成")


def generate_server_cert(server_cert_file, server_key_file, ca_cert_file, ca_key_file):
    # 加载CA证书和密钥
    with open(ca_cert_file, "rb") as f:
        ca_cert = x509.load_pem_x509_certificate(f.read())
    with open(ca_key_file, "rb") as f:
        ca_key = serialization.load_pem_private_key(f.read(), password=None)

    # 生成服务器密钥
    server_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

    # 创建服务器证书请求
    subject = x509.Name(
        [
            x509.NameAttribute(NameOID.COUNTRY_NAME, "CN"),
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "Zhejiang"),
            x509.NameAttribute(NameOID.LOCALITY_NAME, "Hangzhou"),
            x509.NameAttribute(
                NameOID.ORGANIZATION_NAME, "Netease PC Game Loginer Project"
            ),
            x509.NameAttribute(NameOID.COMMON_NAME, "service.mkey.163.com"),
        ]
    )
    server_cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(ca_cert.subject)
        .public_key(server_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.datetime.now(datetime.UTC))
        .not_valid_after(
            datetime.datetime.now(datetime.UTC) + datetime.timedelta(days=365)
        )
        .add_extension(
            x509.SubjectAlternativeName([x509.DNSName("service.mkey.163.com")]),
            critical=False,
        )
        .sign(ca_key, hashes.SHA256())
    )

    # 保存服务器证书和密钥
    with open(server_cert_file, "wb") as f:
        f.write(server_cert.public_bytes(serialization.Encoding.PEM))
    with open(server_key_file, "wb") as f:
        f.write(
            server_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.NoEncryption(),
            )
        )
    info("服务器密钥已生成")


def install_certificate(cert_path):
    system = platform.system()
    try:
        if system == "Linux":
            dest = "/usr/local/share/ca-certificates/netease_game_loginer_root_ca.crt"
            shutil.copy(cert_path, dest)
            subprocess.run(["update-ca-certificates"], check=True)
            info(f"证书已安装到 {dest}")
        elif system == "Windows":
            subprocess.run(
                ["certutil", "-addstore", "Root", cert_path], check=True, shell=True
            )
            info("证书已添加到Windows根存储")
        elif system == "Darwin":
            subprocess.run(
                [
                    "sudo",
                    "security",
                    "add-trusted-cert",
                    "-d",
                    "-r",
                    "trustRoot",
                    "-k",
                    "/Library/Keychains/System.keychain",
                    cert_path,
                ],
                check=True,
            )
            info("证书已添加到macOS系统钥匙串")
        else:
            raise NotImplementedError("不支持的操作系统")
    except Exception as e:
        error(f"安装失败: {str(e)}")


def uninstall_certificate(cert_path):
    system = platform.system()
    try:
        if system == "Linux":
            dest = "/usr/local/share/ca-certificates/test_root_ca.crt"
            if os.path.exists(dest):
                os.remove(dest)
                subprocess.run(["update-ca-certificates", "--fresh"], check=True)
                info("证书已卸载")
            else:
                warning("未找到证书")
        elif system == "Windows":
            subprocess.run(
                ["certutil", "-delstore", "Root", os.path.basename(cert_path)],
                check=True,
                shell=True,
            )
            info("证书已从Windows根存储移除")
        elif system == "Darwin":
            subprocess.run(
                ["sudo", "security", "remove-trusted-cert", "-d", cert_path], check=True
            )
            info("证书已从macOS钥匙串移除")
        else:
            raise NotImplementedError("不支持的操作系统")
    except Exception as e:
        error(f"卸载失败: {str(e)}")


def check_ca_certs_exist(
    ca_crt: str = None, ca_key: str = None, mitmproxy_ca_pem: str = None
) -> bool:
    """检查CA证书文件是否存在"""
    # 如果未提供CA证书路径，则从配置文件中读取
    if not all((ca_crt, ca_key, mitmproxy_ca_pem)):
        debug("未指定CA证书路径，默认从配置文件中读取")
        try:
            ca_crt = Path(cfg["certs_path"]["ca_cert"])
            ca_key = Path(cfg["certs_path"]["ca_key"])
            mitmproxy_ca_pem = Path(cfg["certs_path"]["mitmproxy_ca_cert"])
        except KeyError:
            warning("配置文件中未找到CA证书路径")
            return False
    else:
        ca_crt = Path(ca_crt)
        ca_key = Path(ca_key)
        mitmproxy_ca_pem = Path(mitmproxy_ca_pem)
    # 检查文件是否存在
    try:
        if not all(f.exists() for f in (ca_crt, ca_key, mitmproxy_ca_pem)):
            warning("CA证书缺失")
            return False
        return True
    except Exception as e:
        error(f"检查CA证书时失败: {e}")
        return False


def check_ca_certs_install() -> bool:
    """检查CA证书文件是否已被安装"""
    system = platform.system()
    try:
        if system == "Linux":
            result = subprocess.run(
                [
                    "grep",
                    "-l",
                    "Netease PC Game Loginer Root CA",
                    "/etc/ssl/certs/ca-certificates.crt",
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            return result.returncode == 0
        elif system == "Windows":
            result = subprocess.run(
                ["certutil", "-verifystore", "Root", "Netease PC Game Loginer Root CA"],
                check=False,
                capture_output=True,
                text=True,
                shell=True,
            )
            return "Netease PC Game Loginer Root CA" in result.stdout
        elif system == "Darwin":
            result = subprocess.run(
                [
                    "security",
                    "find-certificate",
                    "-c",
                    "Netease PC Game Loginer Root CA",
                    "/Library/Keychains/System.keychain",
                ],
                check=False,
                capture_output=True,
                text=True,
            )
            return result.returncode == 0
        else:
            raise NotImplementedError("不支持的操作系统")
    except Exception as e:
        error(f"检查CA证书安装时失败: {e}")
        return False


def build_new_ca_certs() -> bool:
    """构建新的CA证书"""
    try:
        generate_ca_cert("ca.crt", "ca.key")
        generate_ca_cert_for_mitmproxy("mitmproxy-ca.pem", "ca.crt", "ca.key")
        info("CA证书已生成")
        return move_ca_certs()
    except Exception as e:
        error(f"构建CA证书时失败: {e}")
        return False


def move_ca_certs(
    ca_crt: str = "ca.crt",
    ca_key: str = "ca.key",
    mitmproxy_ca_pem: str = "mitmproxy-ca.pem",
) -> bool:
    """移动CA证书到ProgramData/NetEase_PC_Game_Loginer目录下"""
    if check_ca_certs_exist(ca_crt, ca_key, mitmproxy_ca_pem):
        try:
            certs_path = Path(cfg["app_dir"]) / "certs"
            certs_path.mkdir(exist_ok=True)
            for f in (ca_crt, ca_key, mitmproxy_ca_pem):
                shutil.move(f, certs_path / f)
            info("CA证书已移动到应用目录")
            cfg["certs_path"]["ca_cert"] = str(certs_path / ca_crt)
            cfg["certs_path"]["ca_key"] = str(certs_path / ca_key)
            cfg["certs_path"]["mitmproxy_ca_cert"] = str(certs_path / mitmproxy_ca_pem)
            return True
        except Exception as e:
            error(f"构建并移动CA证书时失败: {e}")
            return False
    else:
        warning("CA证书不存在或还未创建")
        return False


if __name__ == "__main__":
    # 生成CA证书和服务器证书
    # ca_cert = "ca.crt"
    # ca_key = "ca.key"
    # server_cert = "server.crt"
    # server_key = "server.key"
    # mitmproxy_ca_cert = "mitmproxy-ca.pem"

    # generate_ca_cert(ca_cert, ca_key)
    # generate_ca_cert_for_mitmproxy(mitmproxy_ca_cert, ca_cert, ca_key)
    # generate_server_cert(server_cert, server_key, ca_cert, ca_key)

    # if not os.path.exists(ca_cert):
    #     generate_ca_cert(ca_cert, ca_key)
    #     generate_server_cert(server_cert, server_key, ca_cert, ca_key)
    #     generate_ca_cert_for_mitmproxy(mitmproxy_ca_cert, ca_cert, ca_key)
    #     print("已生成CA,服务器证书,mitmproxy-ca.pem")

    # 安装CA证书
    # install_certificate(ca_cert)

    # 示例：卸载证书
    # uninstall_certificate(ca_cert)

    print(check_ca_certs_install())
