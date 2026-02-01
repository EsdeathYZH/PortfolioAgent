# -*- coding: utf-8 -*-
"""
用户配置加载器

从环境变量加载用户配置

配置格式：USER_XXX="user1:value1;user2:value2"
例如：USER_STOCKS="allen:a,b;hong:c,d"
"""

import logging
import os
from typing import Dict, List, Optional

from core.domain.user import UserConfig

logger = logging.getLogger(__name__)


class UserConfigLoader:
    """从环境变量加载用户配置"""

    def _parse_multi_user_env(self, env_name: str) -> Dict[str, str]:
        """
        解析多用户环境变量格式：USER_XXX="user1:value1;user2:value2"

        Args:
            env_name: 环境变量名，如 "USER_STOCKS"

        Returns:
            字典，格式：{username: value}
        """
        env_value = os.getenv(env_name, "").strip()
        if not env_value:
            return {}

        result = {}
        # 按分号分割用户配置
        for user_config in env_value.split(";"):
            user_config = user_config.strip()
            if not user_config:
                continue

            # 按冒号分割用户名和值
            if ":" not in user_config:
                logger.warning(f"环境变量 {env_name} 中的配置格式错误（缺少冒号）: {user_config}")
                continue

            username, value = user_config.split(":", 1)
            username = username.strip()
            value = value.strip()

            if username and value:
                result[username] = value
            else:
                logger.warning(f"环境变量 {env_name} 中的配置格式错误: {user_config}")

        return result

    def _get_user_value(self, env_name: str, username: str) -> str:
        """
        获取用户配置值

        Args:
            env_name: 环境变量名（不含 USER_ 前缀），如 "STOCKS", "EMAIL_SENDER"
            username: 用户名

        Returns:
            配置值，如果不存在返回空字符串
        """
        multi_user_env = f"USER_{env_name}"
        multi_user_dict = self._parse_multi_user_env(multi_user_env)
        return multi_user_dict.get(username, "")

    def load_users(self) -> List[UserConfig]:
        """
        加载所有用户配置

        Returns:
            用户配置列表

        Raises:
            ValueError: 如果配置不完整或无效
        """
        # 读取用户列表
        users_str = os.getenv("USERS", "").strip()
        if not users_str:
            raise ValueError("未配置用户，请在环境变量中设置 USERS（例如：USERS=user1,user2）")

        usernames = [u.strip() for u in users_str.split(",") if u.strip()]
        if not usernames:
            raise ValueError("USERS 环境变量为空，请至少配置一个用户")

        user_configs = []
        skipped_users = []
        for username in usernames:
            try:
                user_config = self.load_user_config(username)
                if user_config:
                    user_configs.append(user_config)
                else:
                    skipped_users.append(username)
                    logger.warning(f"用户 {username} 配置无效，已跳过")
            except ValueError as e:
                skipped_users.append(username)
                logger.warning(f"加载用户 {username} 配置失败: {e}，已跳过该用户")

        if not user_configs:
            raise ValueError("未成功加载任何用户配置，请检查环境变量配置")

        if skipped_users:
            logger.warning(f"已跳过 {len(skipped_users)} 个用户（配置缺失或不完整）: {skipped_users}")

        logger.info(f"成功加载 {len(user_configs)} 个用户配置: {[u.username for u in user_configs]}")
        return user_configs

    def load_user_config(self, username: str) -> Optional[UserConfig]:
        """
        加载指定用户的配置

        Args:
            username: 用户名

        Returns:
            用户配置对象，如果配置无效返回 None

        Raises:
            ValueError: 如果必需配置缺失
        """
        # 读取股票列表（必需）
        stocks_str = self._get_user_value("STOCKS", username)
        stocks = [s.strip() for s in stocks_str.split(",") if s.strip()]

        if not stocks:
            raise ValueError(
                f'用户 {username} 未配置股票列表，请设置 USER_STOCKS（格式：USER_STOCKS="user1:stocks1;user2:stocks2"）'
            )

        # 读取渠道配置
        channels = {}

        # Email 渠道
        email_sender = self._get_user_value("EMAIL_SENDER", username)
        if email_sender:
            email_password = self._get_user_value("EMAIL_PASSWORD", username)
            if not email_password:
                raise ValueError(f"用户 {username} 配置了 EMAIL_SENDER 但未配置 EMAIL_PASSWORD")
            email_receivers_str = self._get_user_value("EMAIL_RECEIVERS", username)
            email_receivers = (
                [r.strip() for r in email_receivers_str.split(",") if r.strip()] if email_receivers_str else []
            )
            if not email_receivers:
                email_receivers = [email_sender]  # 默认发给自己

            channels["email"] = {
                "sender": email_sender,
                "password": email_password,
                "receivers": email_receivers,
            }

        # ServerChan 渠道
        serverchan_key = self._get_user_value("SERVERCHAN_SEND_KEY", username)
        if serverchan_key:
            channels["serverchan"] = {
                "send_key": serverchan_key,
                "channel": self._get_user_value("SERVERCHAN_CHANNEL", username) or None,
                "noip": self._get_user_value("SERVERCHAN_NOIP", username).lower() == "true",
            }

        # 企业微信渠道
        wechat_url = self._get_user_value("WECHAT_WEBHOOK_URL", username)
        if wechat_url:
            max_bytes_str = self._get_user_value("WECHAT_MAX_BYTES", username)
            max_bytes = int(max_bytes_str) if max_bytes_str else 4000
            channels["wechat"] = {
                "webhook_url": wechat_url,
                "max_bytes": max_bytes,
            }

        # 飞书渠道
        feishu_url = self._get_user_value("FEISHU_WEBHOOK_URL", username)
        if feishu_url:
            max_bytes_str = self._get_user_value("FEISHU_MAX_BYTES", username)
            max_bytes = int(max_bytes_str) if max_bytes_str else 20000
            channels["feishu"] = {
                "webhook_url": feishu_url,
                "max_bytes": max_bytes,
            }

        # Telegram 渠道
        telegram_bot_token = self._get_user_value("TELEGRAM_BOT_TOKEN", username)
        telegram_chat_id = self._get_user_value("TELEGRAM_CHAT_ID", username)
        if telegram_bot_token and telegram_chat_id:
            channels["telegram"] = {
                "bot_token": telegram_bot_token,
                "chat_id": telegram_chat_id,
            }

        # Pushover 渠道
        pushover_user_key = self._get_user_value("PUSHOVER_USER_KEY", username)
        pushover_api_token = self._get_user_value("PUSHOVER_API_TOKEN", username)
        if pushover_user_key and pushover_api_token:
            channels["pushover"] = {
                "user_key": pushover_user_key,
                "api_token": pushover_api_token,
            }

        # Custom Webhook 渠道
        custom_webhook_urls_str = self._get_user_value("CUSTOM_WEBHOOK_URLS", username)
        if custom_webhook_urls_str:
            custom_webhook_urls = [u.strip() for u in custom_webhook_urls_str.split(",") if u.strip()]
            if custom_webhook_urls:
                bearer_token = self._get_user_value("CUSTOM_WEBHOOK_BEARER_TOKEN", username)
                channels["custom"] = {
                    "webhook_urls": custom_webhook_urls,
                    "bearer_token": bearer_token or None,
                }

        # 验证至少配置了一个渠道
        if not channels:
            raise ValueError(
                f"用户 {username} 未配置任何通知渠道，请至少配置一个（Email、ServerChan、企业微信、飞书等）"
            )

        return UserConfig(username=username, stocks=stocks, channels=channels)
