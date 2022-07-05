from argparse import ArgumentParser
import logging
from webmacs import variables, main, keymaps, commands, session, application, hooks


logger = logging.getLogger()


def save_session(*args, **kwargs):
    """
    Save windows and buffers.
    """
    if variables.get("save-session-on-buffer-event"):
        session.session_save(application.app().profile.session_file)
        logger.info("Saving Session")


def init_custom_variables():
    variables.define_variable(
        "save-session-on-buffer-event",
        "If set to True, the session file will get updated every time" +
        " a buffer is opened or closed.",
        False,
        type=variables.Bool())
    variables.define_variable(
        "always-restore-session",
        "Always restore session regardless of whether a URL is given on cmdline",
        True,
        type=variables.Bool())


def set_variables():
    """Set values to variables."""
    variables.set("visited-links-display-limit", 10000)
    variables.set("save-session-on-buffer-event", True)


def init_hooks():
    hooks.webbuffer_closed.add(save_session)
    # added to load_finished as create gives some error
    hooks.webbuffer_load_finished.add(save_session)


def init_custom_keys():
    """Custom Keys are defined in this function LOL"""
    # NOTE: Custom keymap from here, though there should be a user
    #       keymap input file
    content_edit_keymap = keymaps.keymap("webcontent-edit")
    content_edit_keymap.define_key("C-v", "scroll-page-down")
    content_edit_keymap.define_key("M-v", "scroll-page-up")
    content_edit_keymap.define_key("M->", "scroll-bottom")
    content_edit_keymap.define_key("M-<", "scroll-top")
    webbuffer_keymap = keymaps.keymap("webbuffer")
    webbuffer_keymap.define_key("c 0", "copy-current-buffer-url")
    webbuffer_keymap.define_key("j", "send-key-down")
    webbuffer_keymap.define_key("k", "send-key-up")
    # NOTE: standard text selection bindings may work the same in caret browsing mode
    webbuffer_keymap.define_key("C-F", "content-edit-forward-char")
    webbuffer_keymap.define_key("C-B", "content-edit-backward-char")
    webbuffer_keymap.define_key("M-F", "content-edit-forward-word")
    webbuffer_keymap.define_key("M-B", "content-edit-backward-word")
    webbuffer_keymap.define_key("M-E", "content-edit-end-of-line")


def init_custom_webjumps():
    "Custom webjumps, like custom keys"
    commands.webjump.define_webjump("scholar",
                                    "https://scholar.google.com/scholar?hl=en&q=%s",
                                    "Scholar Search")
    commands.webjump.define_webjump("bing",
                                    "https://www.bing.com/search?q=%s&form=QBLH"
                                    "Bing Search")


def init_custom_commands():
    "Whatever custom commands you'd want to create"
    @commands.define_command("go-up")
    def go_up(ctx):
        """Navigate upwards with respect to URL in current buffer.

        A state per webbuffer is tracked and kept in _base_url. If we go up but
        base_url remains the same, e.g. going up from
        "http://somewebsite.com/somedir/somepage.html" lands on
        "http://somewebsite.com/somedir/" which redirects to
        "http://somewebsite.com/somedir/index.html" then we go further up next
        time to "http://somewebsite.com/"

        """
        url = str(ctx.buffer.url().toEncoded(), "utf-8")
        url = url if not url.endswith("/") else url[:-1]
        url = "/".join(url.split("/")[:-1])
        if hasattr(ctx.buffer, "_base_url"):
            if ctx.buffer._base_url == url:
                url = "/".join(url[:-1].split("/")[:-1])
        logger.debug(f"[DEBUG] {url}")
        ctx.buffer._base_url = url
        ctx.buffer.load(url)

    @commands.define_command("set-variable")
    def set_variable(ctx):
        """Set a value for a named variable.
        """
        # We have to implement a function which reads a variable from a prompt
        # like in [[file:~/lib/webmacs/webmacs/commands/global.py::class BookmarkAddPrompt(Prompt):][bookmark prompt]] and that parses the type
        pass


    keymaps.keymap("webbuffer").define_key("u", "go-up")


def init(opts, user_opts):
    parser = ArgumentParser()
    parser.add_argument("--proxy", type=str, default="")
    parser.add_argument("--proxy-dns", action="store_true")
    args = parser.parse_args(user_opts)
    # TODO: Set checks for args.proxy
    if args.proxy:
        logger.info(f"Setting proxy as {args.proxy}")
        variables.set("proxy", args.proxy)
        # TODO: Only if socks proxy
        if args.proxy_dns:
            logger.info(f"DNS requests will also be proxied")
            variables.set("proxy-dns-requests", True)
    init_custom_keys()
    init_custom_commands()
    init_custom_webjumps()
    init_custom_variables()
    set_variables()
    init_hooks()
    if opts.url:
        logger.info("{} was given as a command line argument".format(opts.url))
    main.init(opts)
