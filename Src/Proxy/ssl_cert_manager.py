from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
import datetime
import os
import platform
import subprocess
import shutil


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


def install_certificate(cert_path):
    system = platform.system()
    try:
        if system == "Linux":
            dest = "/usr/local/share/ca-certificates/test_root_ca.crt"
            shutil.copy(cert_path, dest)
            subprocess.run(["update-ca-certificates"], check=True)
            print(f"证书已安装到 {dest}")
        elif system == "Windows":
            subprocess.run(
                ["certutil", "-addstore", "Root", cert_path], check=True, shell=True
            )
            print("证书已添加到Windows根存储")
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
            print("证书已添加到macOS系统钥匙串")
        else:
            raise NotImplementedError("不支持的操作系统")
    except Exception as e:
        print(f"安装失败: {str(e)}")


def uninstall_certificate(cert_path):
    system = platform.system()
    try:
        if system == "Linux":
            dest = "/usr/local/share/ca-certificates/test_root_ca.crt"
            if os.path.exists(dest):
                os.remove(dest)
                subprocess.run(["update-ca-certificates", "--fresh"], check=True)
                print("证书已卸载")
            else:
                print("未找到证书")
        elif system == "Windows":
            subprocess.run(
                ["certutil", "-delstore", "Root", os.path.basename(cert_path)],
                check=True,
                shell=True,
            )
            print("证书已从Windows根存储移除")
        elif system == "Darwin":
            subprocess.run(
                ["sudo", "security", "remove-trusted-cert", "-d", cert_path], check=True
            )
            print("证书已从macOS钥匙串移除")
        else:
            raise NotImplementedError("不支持的操作系统")
    except Exception as e:
        print(f"卸载失败: {str(e)}")


if __name__ == "__main__":
    # 生成CA证书和服务器证书
    ca_cert = "ca.crt"
    ca_key = "ca.key"
    server_cert = "server.crt"
    server_key = "server.key"
    mitmproxy_ca_cert = "mitmproxy-ca.pem"

    # generate_ca_cert(ca_cert, ca_key)
    # generate_ca_cert_for_mitmproxy(mitmproxy_ca_cert, ca_cert, ca_key)
    generate_server_cert(server_cert, server_key, ca_cert, ca_key)

    # if not os.path.exists(ca_cert):
    #     generate_ca_cert(ca_cert, ca_key)
    #     generate_server_cert(server_cert, server_key, ca_cert, ca_key)
    #     generate_ca_cert_for_mitmproxy(mitmproxy_ca_cert, ca_cert, ca_key)
    #     print("已生成CA,服务器证书,mitmproxy-ca.pem")

    # 安装CA证书
    # install_certificate(ca_cert)

    # 示例：卸载证书
    # uninstall_certificate(ca_cert)
