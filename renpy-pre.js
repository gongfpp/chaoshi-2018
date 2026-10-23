/*

Copyright 2019-2021 Sylvain Beucler
Copyright 2022 Teyut <teyut@free.fr>
Copyright 2019-2022 Tom Rothamel <pytom@bishoujo.us>

Permission is hereby granted, free of charge, to any person
obtaining a copy of this software and associated documentation files
(the "Software"), to deal in the Software without restriction,
including without limitation the rights to use, copy, modify, merge,
publish, distribute, sublicense, and/or sell copies of the Software,
and to permit persons to whom the Software is furnished to do so,
subject to the following conditions:

The above copyright notice and this permission notice shall be
included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
*/

Module = window.Module || { };
Module.preRun = Module.preRun || [ ];

(function () {

    /***************************************************************************
     * Report messages, errors, and progress.
     **************************************************************************/

    // The div containing the status and progress bar.
    let statusDiv = document.getElementById("statusDiv");
    let statusTextDiv = document.getElementById("statusTextDiv");
    let statusProgress = document.getElementById("statusProgress");

    // Presplash block
    let presplash = document.getElementById('presplash');

    // The timeout before the status div hides itself.
    let statusTimeout = null;

    // The status message.
    let statusText = "";

    // How long before the status div starts hiding, in seconds.
    const STATUS_TIMEOUT = 5000;

    // The last time the progress was updated.
    let lastProgressTime = 0;

    // Has an error been reported?
    let errorReported = false;

    // Should output only go to the console?
    let printConsoleOnly = false;

    /**
     * Hide the status div. Once it's hidden, clears the status text.
     */
    function hideStatus() {
        if (errorReported) {
            return;
        }

        statusDiv.classList.remove("visible");
        statusDiv.classList.add("hidden");

        statusTimeout = setTimeout(() => {
            statusText = "";
        }, 250);
    }

    /**
     * Show the status div.
     */
    function showStatus() {
        statusDiv.classList.remove("hidden");
        statusDiv.classList.add("visible");
        statusTextDiv.scrollTop = statusTextDiv.scrollHeight;
        statusProgress.style.display = "none";
    }

    /**
     * Cancels the timeout that hides the status div.
     */
    function cancelStatusTimeout() {
        if (statusTimeout) {
            clearTimeout(statusTimeout);
            statusTimeout = null;
        }
    }

    /**
     * Start the timeout that hides the status div.
     */
    function startStatusTimeout() {
        cancelStatusTimeout();
        statusTimeout = setTimeout(hideStatus, STATUS_TIMEOUT);
    }

    function printCommon(s) {

        cancelStatusTimeout();
        lastProgressTime = 0;

        if (statusText) {
            statusText += "<br>";
        }

        if (s == "" && !errorReported) {
            statusText = "";
            return;
        }

        for (let i of s.split("\n")) {
            if (i.length > 0) {
                console.log(i);
            }
        }

        if (printConsoleOnly) {
            return;
        }

        s = String(s);
        s = s.replace(/&/g, "&amp;");
        s = s.replace(/</g, "&lt;");
        s = s.replace(/>/g, "&gt;");
        s = s.replace('\n', '<br />', 'g');

        statusText += s;

        let lines = statusText.split("<br />");
        if (lines.length > 200) {
            lines = lines.slice(lines.length - 200);
            statusText = lines.join("<br />");
        }

        statusTextDiv.innerHTML = statusText;

        showStatus();
    }

    /**
     * Reports a message that will eventually be hidden.
     */
    function printMessage(s) {

        if (s.startsWith("warning: ") || s.startsWith("wasm streaming compile failed") || s.startsWith("falling back to ArrayBuffer") ) {
            console.log(s);
            return;
        }

        printCommon(s);
        startStatusTimeout();
    }

    function reportError(s, e) {
        if (e) {
            console.error(e, e.stack);
            s += ": " + e.message;
        }

        s += "\nMore information may be available in the browser console or contained in the log.";

        printCommon(s);

        errorReported = true;

        try {
            Module.addRunDependency("error");
        } catch (e) {
            window.stop();
        }
    }

    /**
     * Updates the progress bar.
     */
    function progress(done, total) {

        if (errorReported) {
            return;
        }

        let now = +Date.now();

        if ((now < lastProgressTime + 32) && (done < total) && (done > 1)) {
            return
        }

        lastProgressTime = now;

        cancelStatusTimeout();
        showStatus();

        if (total) {
            statusProgress.value = done;
            statusProgress.max = total;
            statusProgress.style.display = "block";
        }

        startStatusTimeout();

    }

    window.progress = progress;

    Module.print = printMessage;
    Module.printErr = printMessage;


    /***************************************************************************
     * Browser capability checks.
     **************************************************************************/

    // Report the lack of WebAssembly support.
    if (typeof WebAssembly !== 'object') {
        reportError("This browser does not support WebAssembly.");
    }

    // Report the lack of the fetch function.
    if (typeof fetch !== 'function') {
        reportError("This browser does not support fetch.");
    }

    // Clear error when running without a server.
    if (location.href.startsWith('file://')) {
        reportError("This browser requires the game to be run from a web server (i.e. double-clicking on index.html won't work).");
    }


    /***************************************************************************
     * Emscripten initialization and termination.
     **************************************************************************/

    /** Set up the canvas. */
    let canvas = document.getElementById('canvas');

    /** Set when the webGlContext is lost. */
    window.webglContextLost = false;

    /** Set when the webGlContext is restored. Cleared by Ren'Py in core.py. */
    window.webglContextRestored = false;

    canvas.addEventListener("webglcontextlost", (e) => {
        window.webglContextRestored = false;
        window.webglContextLost = true;
        e.preventDefault();
    }, false);

    canvas.addEventListener("webglcontextrestored", (e) => {
        window.webglContextLost = false;
        window.webglContextRestored = true;
    }, false);


    canvas.addEventListener('mouseenter', function (e) { window.focus() });

    canvas.addEventListener('click', function (e) { window.focus() });

    Module.canvas = canvas;

    window.presplashEnd = () => {
        presplash.remove();
        cancelStatusTimeout();
        hideStatus();
    };

    window.atExit = () => {
        canvas.remove();
        reportError("The game exited unexpectedly.");
    };

    Module.onAbort = () => {
        canvas.remove();
        reportError("The game aborted unexpectedly.");
    };

    /**
     * Initialize the filesystem.
     */
    function initFs() {
        // Create the save directory, and mount the IDBFS filesystem.
        try {
            Module.addRunDependency('initFs');
            FS.mkdir('/home/web_user/.renpy');
            FS.mount(IDBFS, {}, '/home/web_user/.renpy');
            FS.syncfs(true, (err) => {
                if (err) {
                    printMessage("Error syncing IDBFS: " + err);
                    printMessage("The game may not be able to save properly.");
                }

                Module.removeRunDependency('initFs');
            });
        } catch (e) {
            reportError("Could not create ~/.renpy/", e);
        }
    }

    Module.preRun.push(initFs);

    // The size of the data and gamezip files.
    let dataSize = 0;
    let gameZipSize = 0;

    // The number of bytes downloaded.
    let dataDownloaded = 0;
    let gameZipDownloaded = 0;

    // Have we issued the data and gameZip prompts?
    let dataPrompt = false;
    let gameZipPrompt = false;

    function updateDownloadProgress() {
        if (dataSize == 0) {
            return;
        }

        if (dataDownloaded < dataSize || gameZipSize == 0) {
            if (!dataPrompt) {
                printMessage("");
                printMessage("Downloading engine...");
                dataPrompt = true;
            }

            progress(dataDownloaded, dataSize);
            return;
        }

        if (!gameZipPrompt) {
            printMessage("");
            printMessage("Downloading game data...");
            gameZipPrompt = true;
        }

        progress(gameZipDownloaded, gameZipSize);

    }

    Module.setStatus = function (s) {

        var m = s.match(/([^(]+)\((\d+(\.\d+)?)\/(\d+)\)/);

        if (m) {
            dataDownloaded = parseInt(m[2]);
            dataSize = parseInt(m[4]);
            updateDownloadProgress();
            return;
        }

        console.log(s);
    }

            /* CHAOSHI_LOADER_V2 */
    // ---- 并行分片 + 空闲超时 + 后台预取（由 tools/patch_web.py 注入）------
    // 与 Windows 无关的三条约束：
    //   1) 不能用墙钟超时判失败 —— 弱网是「慢」不是「死」，只有连续 IDLE_MS
    //      收不到字节才算断流（Cloudflare 不支持 Range，断了就得从头再来）。
    //   2) 进度只认 Σ st.got 一个账本，重下不能让进度条倒退或溢出。
    //   3) 落盘后必须核对字节数，截断的 zip 会让 Ren'Py 报 BadZipFile，
    //      不如在这里就说清楚。
    var CS = window.ChaoshiLoader || null;
    var GAME_FILE = null;
    var GAME_PARTS = [];
    var PREFETCH = null;

    var PART_CONC = 3;          // 弱网下 3 条流比 4 条更容易各自跑满
    var IDLE_MS = 15000;        // 连续 15 秒零字节才判定断流
    var ATTEMPT_MS = 180000;    // 单次尝试的墙钟兜底（不是主判据）
    var MAX_TRIES = 6;

    function csLog(s) { if (CS && CS.log) { CS.log(s); } }

    function csSleep(ms) {
        return new Promise(function (r) { setTimeout(r, ms); });
    }

    function zipBytes() {
        var n = 0;
        for (var i = 0; i < GAME_PARTS.length; i++) { n += GAME_PARTS[i].got; }
        return gameZipSize ? Math.min(n, gameZipSize) : n;
    }

    function reportZip() {
        if (CS && CS.zipProgress) { CS.zipProgress(zipBytes(), gameZipSize); }
    }

    function bootFail(kind, detail) {
        // 有自绘 UI 就走自绘；没有（理论上不会）退回原生报错，至少别白屏
        if (CS && CS.fatal) {
            CS.fatal(kind, detail);
        } else {
            reportError('Could not download game data', { message: String(detail || '') });
        }
    }

    function partsMeta() {
        var names = window.gameZipParts || [];
        var sizes = window.gameZipPartSizes || [];
        var total = 0;
        for (var i = 0; i < sizes.length; i++) { total += sizes[i] || 0; }
        return { names: names, sizes: sizes, total: window.gameZipTotal || total };
    }

    // 单次尝试：一次 fetch + 读完整个 body。返回的 Promise 只有在
    // 「本片已经收满」或「确定失败」时才会落定。
    function pullPart(st) {
        return new Promise(function (resolve, reject) {
            var ctrl = new AbortController();
            var lastByte = Date.now();
            var done = false;

            var idle = setInterval(function () {
                if (Date.now() - lastByte > IDLE_MS) {
                    try { ctrl.abort(); } catch (e) {}
                }
            }, 2000);
            var wall = setTimeout(function () {
                try { ctrl.abort(); } catch (e) {}
            }, ATTEMPT_MS);

            function finish(err) {
                if (done) { return; }
                done = true;
                clearInterval(idle);
                clearTimeout(wall);
                if (err) { reject(err); } else { resolve(); }
            }

            var wantFrom = st.got;
            var opt = { cache: 'default', signal: ctrl.signal };
            if (wantFrom > 0) { opt.headers = { 'Range': 'bytes=' + wantFrom + '-' }; }

            // 服务端忽略 Range（Cloudflare 返回 200 全量）时，body 是从 0 开始的，
            // 要把前面已经收到过的字节读掉再接着算，否则 zip 会整体错位。
            var skip = 0;

            fetch(st.url, opt).then(function (r) {
                if (!r.ok && r.status !== 206) {
                    throw new Error('HTTP ' + r.status + ' ' + r.statusText);
                }
                st.status = r.status;
                skip = (r.status === 206) ? 0 : wantFrom;
                if (!r.body || !r.body.getReader) {
                    return r.arrayBuffer().then(function (buf) {
                        var u8 = new Uint8Array(buf);
                        if (skip > 0) { u8 = u8.subarray(skip); skip = 0; }
                        lastByte = Date.now();
                        st.chunks.push(u8);
                        st.got += u8.length;
                        reportZip();
                    });
                }
                var reader = r.body.getReader();
                function pump() {
                    return reader.read().then(function (c) {
                        if (c.done) { return; }
                        lastByte = Date.now();
                        var v = c.value;
                        if (skip > 0) {
                            if (v.length <= skip) { skip -= v.length; return pump(); }
                            v = v.subarray(skip);
                            skip = 0;
                        }
                        st.chunks.push(v);
                        st.got += v.length;
                        reportZip();
                        return pump();
                    });
                }
                return pump();
            }).then(function () {
                if (st.size && st.got < st.size) {
                    throw new Error('分片不完整 ' + st.got + '/' + st.size);
                }
                finish(null);
            }).catch(function (e) {
                finish(e);
            });
        });
    }

    async function pullWithRetry(st) {
        var tries = 0;
        while (!st.size || st.got < st.size) {
            tries += 1;
            try {
                await pullPart(st);
            } catch (e) {
                st.lastErr = e;
                if (tries >= MAX_TRIES) {
                    throw new Error('分片 ' + st.url + ' 连续 ' + tries + ' 次失败：'
                                    + (e && e.message ? e.message : e));
                }
                csLog('retry ' + st.url + ' #' + tries + '：' + (e && e.message));
                await csSleep(700 * tries);
                continue;
            }
            if (!st.size || st.got >= st.size) { break; }
        }
        st.done = true;
        reportZip();
    }

    function startPrefetch() {
        if (PREFETCH) { return PREFETCH; }
        var m = partsMeta();
        GAME_PARTS = m.names.map(function (n, i) {
            return {
                url: n, size: m.sizes[i] || 0,
                chunks: [], got: 0, done: false, status: 0
            };
        });
        gameZipSize = m.total;
        if (CS && CS.zipProgress) { CS.zipProgress(0, gameZipSize); }

        PREFETCH = (async function () {
            var cursor = 0;
            var workers = [];
            for (var w = 0; w < PART_CONC; w++) {
                workers.push((async function () {
                    while (cursor < GAME_PARTS.length) {
                        var st = GAME_PARTS[cursor];
                        cursor += 1;
                        try {
                            await pullWithRetry(st);
                        } catch (e) {
                            st.error = e;
                            csLog('part gave up: ' + st.url);
                        }
                    }
                })());
            }
            await Promise.all(workers);
        })();
        return PREFETCH;
    }

    async function loadGameZip() {
        try {
            var m = partsMeta();
            gameZipSize = m.total;

            await startPrefetch();

            // 预取阶段放弃的分片：这里串行再兜一次（单独跑，不抢带宽）
            for (var i = 0; i < GAME_PARTS.length; i++) {
                var bad = GAME_PARTS[i];
                if (!bad.done) {
                    bad.chunks = bad.chunks || [];
                    await pullWithRetry(bad);
                }
            }

            GAME_FILE = FS.open('/game.zip', 'w');
            var offset = 0;
            for (var k = 0; k < GAME_PARTS.length; k++) {
                var p = GAME_PARTS[k];
                for (var j = 0; j < p.chunks.length; j++) {
                    var b = p.chunks[j];
                    FS.write(GAME_FILE, b, 0, b.length, offset);
                    offset += b.length;
                }
                p.chunks = [];
            }
            FS.close(GAME_FILE);
            GAME_FILE = null;

            var size = FS.stat('/game.zip').size;
            if (size !== gameZipSize) {
                throw new Error('落盘 ' + size + ' 字节，应为 ' + gameZipSize + ' 字节');
            }
            if (CS && CS.zipProgress) { CS.zipProgress(gameZipSize, gameZipSize); }

        } catch (e) {
            if (GAME_FILE) { try { FS.close(GAME_FILE); } catch (x) {} GAME_FILE = null; }
            var msg = (e && e.message) ? e.message : String(e);
            var kind = 'idle';
            if (/HTTP 4\d\d|HTTP 5\d\d/.test(msg)) { kind = 'http'; }
            else if (/不完整|落盘|offset/.test(msg)) { kind = 'incomplete'; }
            csLog('loadGameZip failed: ' + msg);
            bootFail(kind, msg);
        }
    }

    // 立即开始下载，与 wasm 的下载/编译并行
    startPrefetch();
    function runLoadGameZip() {
        Module.addRunDependency('loadGameZip');

        loadGameZip().then(() => {
            Module.removeRunDependency('loadGameZip');
        });

    }

    Module['preRun'].push(runLoadGameZip);

    /***************************************************************************
     *
     **************************************************************************/

    let cmd_queue = [];
    let cur_cmd = undefined;
    let cmd_debug = false;

    function cmd_log(...args) {
        if (cmd_debug) console.debug(...args);
    }

    /** This functions is called by the wrapper script at the end of script execution. */
    function cmd_callback(result) {
        cmd_log('cmd_callback', result);

        if (cur_cmd === undefined) {
            console.error('Unexpected command result', result);
            return;
        }

        try {
            if (result.error !== undefined) {
                cmd_log('ERROR', result.name, result.error, result.traceback);
                const e = new Error(result.error);
                e.name = result.name;
                e.traceback = result.traceback;
                cur_cmd.reject(e);
            } else {
                cmd_log('SUCCESS', result.data);
                cur_cmd.resolve(result.data);
            }
        } finally {
            cur_cmd = undefined;
            send_next_cmd();
        }
    }

    window._renpy_cmd_callback = cmd_callback;

    /** Prepare and send the next command to be executed if any. */
    function send_next_cmd() {
        if (cmd_queue.length == 0) return

        cur_cmd = cmd_queue.shift();
        cmd_log('send_next_cmd', cur_cmd);

        // Convert script to base64 to prevent having to escape
        // the script content as a Python string
        const script_b64 = btoa(cur_cmd.py_script);
        const wrapper = 'import base64, emscripten, json, traceback;\n'
            + 'try:'
            + "result = None;"
            + "exec(base64.b64decode('" + script_b64 + "').decode('utf-8'));"
            + "result = json.dumps(dict(data=result));"
            + "\n"
            + "except Exception as e:"
            + "result = json.dumps(dict(error=str(e), name=e.__class__.__name__, traceback=traceback.format_exc()));"
            + "\n"
            + "emscripten.run_script('_renpy_cmd_callback(%s)' % (result,));";

        cmd_log(wrapper);

        // Write script to the global variable Ren'Py is monitoring
        window._renpy_cmd = wrapper;
    }

    /** Add a command to the queue and execute it if the queue was empty. */
    function add_cmd(py_script, resolve, reject) {
        const cmd = { py_script: py_script, resolve: resolve, reject: reject };
        cmd_log('add_cmd', cmd);
        cmd_queue.push(cmd);

        if (cur_cmd === undefined) send_next_cmd();
    }

    /* Global definitions */

    /** Execute Python statements in Ren'Py Python's thread. The statements are executed
     * using the renpy.python.py_exec() function, and the value of the "result" variable
     * is passed to the resolve callback. In case of error, an Error instance is passed
     * to the reject callback, with an extra "traceback" property.
     * @param py_script The Python script to execute.
     * @return A promise which resolves with the statements result.
     */
    renpy_exec = function (py_script) {
        return new Promise((resolve, reject) => {
            add_cmd(py_script, resolve, reject);
        });
    };

    window.renpy_exec = renpy_exec;

    /** Helper function to get the value of a Ren'Py variable.
     * @param name The variable name (e.g., "build.name").
     * @return A promise which resolves with the variable value.
     */
    renpy_get = function (name) {
        return new Promise((resolve, reject) => {
            renpy_exec('result = ' + name)
                .then(resolve).catch(reject);
        });
    };

    window.renpy_get = renpy_get;

    /** Helper function to set the value of a Ren'Py variable.
     * @param name The variable name (e.g., "build.name").
     * @param value The value to set. It should either be a basic JS type that
     *              will be converted to JSON, or a Python expression. The raw
     *              parameter must be set to true for the latter case.
     * @param raw (optional) If true, value is a valid Python expression.
     *            Otherwise, it must be a basic JS type.
     * @return A promise which resolves with true in case of success
     *         and fails otherwise.
     */
    renpy_set = function (name, value, raw) {
        let script;
        if (raw) {
            script = name + " = " + value + "; result = True";
        } else {
            // Using base64 as it is unclear if we can use the output
            // of JSON.stringify() directly as a Python string
            script = 'import base64, json; '
                + name + " = json.loads(base64.b64decode('"
                + btoa(JSON.stringify(value))
                + "').decode('utf-8')); result = True";
        }
        return new Promise((resolve, reject) => {
            renpy_exec(script)
                .then(resolve).catch(reject);
        });
    };

    window.renpy_set = renpy_set;


    /***************************************************************************
     * Context menu.
     **************************************************************************/

    const menu = document.getElementById('ContextMenu');

    const contextContainer = document.getElementById('ContextContainer');

    document.getElementById('ContextButton').addEventListener('click', function (e) {
        if (menu.style.display == 'none') {
            menu.style.display = 'block';
            contextContainer.classList.add("shown");
        } else {
            menu.style.display = 'none';
            contextContainer.classList.remove("shown");
        }
        e.preventDefault();
    });

    menu.addEventListener('click', function (e) {
        if (e.target.tagName == 'A') {
            // Close context menu when a menu item is selected
            menu.style.display = 'none';
        }
    });

    async function onSavegamesImport(input) {
        reader = new FileReader();
        reader.onload = function (e) {
            FS.writeFile('savegames.zip', new Uint8Array(e.target.result));

            renpy_exec('result = renpy.savelocation.unzip_saves()').then((result) => {
                FS.syncfs(false, function (err) {
                    if (err) {
                        console.trace();
                        console.log(err, err.message);
                        printMessage("Warning: cannot import savegames: write error: " + err.message );
                    } else {
                        renpy_exec('renpy.loadsave.location.scan()').then(result => {
                            printMessage("Saves imported successfully.");
                        }).catch(error => {
                            console.error('Cannot rescan saves folder:', error);
                            printMessage("Saves imported - restart game to apply.");
                        });
                    }
                });
            }).catch(error => {
                console.error('Cannot import savegames', error);
                printMessage("Couldn't import the savegames: " + error.message);
            })
        }
        reader.readAsArrayBuffer(input.files[0])
        input.type = ''; input.type = 'file'; // reset field
    }

    window.onSavegamesImport = onSavegamesImport;

    function onSavegamesExport() {
        renpy_exec('result = renpy.savelocation.zip_saves()').then((ret) => {
            if (ret) {
                FSDownload('savegames.zip', 'application/zip');
                printMessage("Saves exported successfully.\n");
            }
        });
    }

    window.onSavegamesExport = onSavegamesExport;

    function FSDownload(filename, mimetype) {
        console.log('download', filename);
        var a = document.createElement('a');
        a.download = filename.replace(/.*\//, '');
        try {
            a.href = window.URL.createObjectURL(new Blob([FS.readFile(filename)],
                { type: mimetype || '' }));
        } catch (e) {
            Module.print("Error opening " + filename + "\n");
            return;
        }
        document.body.appendChild(a);
        a.click();

        // delay clean-up to avoid iOS issue:
        // The operation couldn’t be completed. (WebKitBlobResource error 1.)
        setTimeout(function () {
            window.URL.revokeObjectURL(a.href);
            document.body.removeChild(a);
        }, 1000);
    }

    window.FSDownload = FSDownload;

    /***************************************************************************
     * Precaching.
     **************************************************************************/

    function loadCache() {

        try {
            navigator.serviceWorker.controller.postMessage(["loadCache"]);
        } catch (e) {
            // pass
        }

        async function loadCacheWorker() {

            let response = await fetch("pwa_catalog.json");
            let catalog = await response.json();

            let cachedCatalog;

            try {
                let cachedCatalogResponse = await fetch("pwa_catalog.json?cached")
                cachedCatalog = await cachedCatalogResponse.json();
            } catch (e) {
                console.log("No cached catalog found.");
                cachedCatalog = { version: -1 };
            }

            if (cachedCatalog.version == catalog.version) {
                return;
            }

            printMessage("");
            printMessage("Preloading game files into browser cache...")
            progress(0, catalog.files.length);

            for (let i = 0; i < catalog.files.length; i++) {
                let response = await fetch(catalog.files[i]);
                await response.blob();

                progress(i + 1, catalog.files.length);
            }

            cancelStatusTimeout();
            hideStatus();

            // This will add the catalog to the cache, such that
            // fetch("pwa_catalog.json?cached") will return it.
            fetch("pwa_catalog.json?uncached");
        }

        loadCacheWorker();
    }

    window.loadCache = loadCache;

    function clearCache() {
        try {
            navigator.serviceWorker.controller.postMessage(["clearCache"]);
        } catch (e) {
            // pass
        }

        localStorage.cacheVersion = -1;
    }

    window.clearCache = clearCache;

    /***************************************************************************
     * Text input.
     **************************************************************************/

    const inputDiv = document.getElementById("inputDiv");
    const inputForm = document.getElementById("inputForm");
    const inputPrompt = document.getElementById("inputPrompt");
    const inputText = document.getElementById("inputText");

    // This stores the input after enter is pressed.
    window.inputResult = null;

    function submitInput(e) {
        e.preventDefault();
        window.inputResult = inputText.value;
    }

    inputForm.addEventListener("submit", submitInput);

    inputDiv.addEventListener("keydown", function (e) { e.stopPropagation(); });
    inputDiv.addEventListener("keyup", function (e) { e.stopPropagation(); });
    inputDiv.addEventListener("keypress", function (e) { e.stopPropagation(); });

    inputDiv.addEventListener("mousemove", function (e) { e.stopPropagation(); });
    inputDiv.addEventListener("mousedown", function (e) { e.stopPropagation(); });
    inputDiv.addEventListener("mouseup", function (e) { e.stopPropagation(); });

    inputDiv.addEventListener("touchstart", function (e) { e.stopPropagation(); });
    inputDiv.addEventListener("touchend", function (e) { e.stopPropagation(); });
    inputDiv.addEventListener("touchcancel", function (e) { e.stopPropagation(); });
    inputDiv.addEventListener("touchmove", function (e) { e.stopPropagation(); });

    let inputAllow = null;
    let inputExclude = null;

    inputText.addEventListener("input", (e) => {
        let newValue = "";

        for (let c of inputText.value) {
            if (inputAllow && !inputAllow.includes(c)) {
                continue;
            }

            if (inputExclude && inputExclude.includes(c)) {
                continue;
            }

            newValue += c;
        }

        if (newValue != inputText.value) {
            let end = inputText.selectionEnd;
            inputText.value = newValue;
            inputText.setSelectionRange(end-1, end-1);
        }
    });


    function startInput(prompt, value, allow, exclude, mask) {
        window.inputResult = null;

        inputDiv.classList.remove("hidden");
        inputDiv.classList.add("visible");

        while (inputPrompt.firstChild) {
            inputPrompt.removeChild(inputPrompt.firstChild);
        }

        let promptText = document.createTextNode(prompt);
        inputPrompt.appendChild(promptText);

        inputText.value = value;
        inputText.focus();

        inputAllow = allow;
        inputExclude = exclude;

        if (mask) {
            inputText.type = "password";
        } else {
            inputText.type = "text";
        }

    }

    window.startInput = startInput;

    function endInput() {
        inputDiv.classList.remove("visible");
        inputDiv.classList.add("hidden");
        inputText.blur();
    }

    window.endInput = endInput;

    /***************************************************************************
     * Fetch.
     ***************************************************************************/

    let fetchId = 1;
    let fetchResult = { };

    /**
     * Fetch a file from the server.
     *
     * @param method The HTTP method to use.
     * @param url The URL to fetch.
     * @param inFile The file to send to the server. A string giving the file name, or null for no file.
     * @param outFile The file to write the response to. A string giving the file name, or null for no file.
     * @param inContentType The content type of the file to send to the server. A string giving the content type. Ignored if inFile is null.
     * @param headers A string containing a JSON object that contains the headers to send to the server.
     *
     * @return A string giving the result of the fetch. The first word is the status, which is one of "OK", "ERROR", or "PENDING", followed by the HTTP status code and status text.
     */
    function fetchFile(method, url, inFile, outFile, inContentType, headers) {

        let id = fetchId++;
        fetchResult[id] = "PENDING Fetch in progress.";

        // Ensure headers exists and is not a copy.
        if (headers) {
            headers = JSON.parse(headers)
        } else {
            headers = { };
        }

        headers = { ...headers };

        async function fetchFileWork() {
            try {

                let content = ''

                if (inFile) {
                    headers["Content-Type"] = inContentType || 'application/octet-stream';
                }

                let options = { method: method, headers: headers};

                if (inFile) {
                    options.body = FS.readFile(inFile, { encoding: 'binary' });
                }

                let response = await fetch(url, options);

                if (response.ok) {
                    if (outFile) {
                        let ab = await response.arrayBuffer();
                        FS.writeFile(outFile, new Uint8Array(ab));
                    }

                    fetchResult[id] = "OK " + response.status + " " + response.statusText;
                } else{
                    fetchResult[id] = "ERROR " + response.status + " " + response.statusText;
                }

            } catch (err) {
                fetchResult[id] = "ERROR " + err;
                console.error(err);
            }

        }

        fetchFileWork();

        return id;
    }

    function fetchFileResult(id) {
        let result = fetchResult[id];

        if (! result.startsWith("PENDING")) {
            delete fetchResult[id];
        }

        return result || "ERROR Fetch ID not found.";
    }

    window.fetchFile = fetchFile;
    window.fetchFileResult = fetchFileResult;

    /**
     * Fullscreen support.
     */

    let lastFullscreenTime = 0;

    function isFullscreen() {
        let now = +new Date();
        return document.fullscreenElement ? 1 : 0;
    }

    window.isFullscreen = isFullscreen;

    function setFullscreen(enable) {

        let current = document.fullscreenElement !== null;

        if (enable == current) {
            return;
        }

        let now = +new Date();

        if (lastFullscreenTime + 250 > +new Date()) {
            return;
        }

        lastFullscreenTime = now;

        setTimeout(function () {
            if (enable) {
                let e = document.getElementsByTagName("html")[0];
                e.requestFullscreen().catch(function (error) {
                    lastFullscreenTime = now + 15000;
                });
            } else {
                document.exitFullscreen();
            }
        }, 0);
    }

    window.setFullscreen = setFullscreen;

    /***************************************************************************
     * "Hidden" developer functions.
     **************************************************************************/

    function downloadBytecode() {
        FSDownload('/game/cache/bytecode-311.rpyb', 'application/octet-stream');
    }

    window.downloadBytecode = downloadBytecode;

    function traceSleep() {
        printConsoleOnly = true;
        renpy_exec('import emscripten; emscripten.TRACE = True')
    }

    window.traceSleep = traceSleep;

    function loseContext() {
        let e = canvas.getContext("webgl2").getExtension("WEBGL_lose_context");
        e.loseContext();

        setTimeout(function () {
            e.restoreContext();
        }, 1000);
    }

    window.loseContext = loseContext;


    /***************************************************************************
     * Overlay div handling.
     **************************************************************************/

    let overlayDiv = document.getElementById("overlayDiv");

    for (let eventName of ["mousedown", "mouseup", "mousemove" ]) {
        overlayDiv.addEventListener(eventName, function (e) {
            canvas.dispatchEvent(new MouseEvent(e.type, e));

            if (e.type == "mouseup") {
                overlayDiv.remove();
            }

        });

    };








})();
