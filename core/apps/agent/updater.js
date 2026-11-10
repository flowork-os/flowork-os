"use strict";
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
Object.defineProperty(exports, "__esModule", { value: true });
exports.updateActions = exports.MenuUpdateStep = void 0;
exports.setAutoUpdateChecking = setAutoUpdateChecking;
exports.broadcastState = broadcastState;
exports.getLastState = getLastState;
exports.initAutoUpdater = initAutoUpdater;
exports.checkForUpdates = checkForUpdates;
exports.quitAndInstall = quitAndInstall;
exports.getHostUpdateStatus = getHostUpdateStatus;
exports.applyHostUpdate = applyHostUpdate;
const electron_1 = require("electron");
const types_1 = require("./types");

var MenuUpdateStep;
(function (MenuUpdateStep) {
    MenuUpdateStep["CheckForUpdates"] = "Check for Updates";
    MenuUpdateStep["CheckingForUpdates"] = "Checking for Updates...";
    MenuUpdateStep["DownloadingUpdate"] = "Downloading Update...";
    MenuUpdateStep["RestartToUpdate"] = "Restart to Update";
})(MenuUpdateStep || (exports.MenuUpdateStep = MenuUpdateStep = {}));

exports.updateActions = {
    [MenuUpdateStep.CheckForUpdates]: () => checkForUpdates(true),
    [MenuUpdateStep.CheckingForUpdates]: undefined,
    [MenuUpdateStep.DownloadingUpdate]: undefined,
    [MenuUpdateStep.RestartToUpdate]: undefined,
};

let updaterInitialized = false;
let lastState = { type: types_1.UpdateState.Idle };

function broadcastState(state) {
    lastState = state;
    for (const win of electron_1.BrowserWindow.getAllWindows()) {
        try {
            win.webContents.send('updater:state-changed', state);
        } catch (e) {}
    }
}

function getLastState() {
    return lastState;
}

function updateMenuState(step) {
    try {
        const menu = electron_1.Menu.getApplicationMenu();
        if (menu) {
            const item = menu.getMenuItemById('check-for-updates');
            if (item) {
                item.label = step;
                item.enabled = exports.updateActions[step] !== undefined;
            }
        }
    } catch (e) {}
}

function startAutoUpdateChecks() {
    // Permanently disabled
}

function stopAutoUpdateChecks() {
    // Permanently disabled
}

function setAutoUpdateChecking(enabled) {
    // Permanently disabled
}

function initAutoUpdater(isHeadless, settingsService) {
    console.log('[AutoUpdater] Auto updater permanently disabled.');
    updaterInitialized = true;
    broadcastState({ type: types_1.UpdateState.Idle });
    updateMenuState(MenuUpdateStep.CheckForUpdates);
}

function checkForUpdates(isManual = false) {
    console.log('[AutoUpdater] Update check skipped: Auto updater is disabled.');
    broadcastState({ type: types_1.UpdateState.Idle });
    updateMenuState(MenuUpdateStep.CheckForUpdates);
    if (isManual) {
        try {
            const win = electron_1.BrowserWindow.getFocusedWindow();
            const options = {
                type: 'info',
                title: 'Check for Updates',
                message: 'Auto updates are permanently disabled.',
                buttons: ['OK'],
            };
            if (win) {
                electron_1.dialog.showMessageBox(win, options);
            } else {
                electron_1.dialog.showMessageBox(options);
            }
        } catch (e) {}
    }
}

function quitAndInstall() {
    console.log('[AutoUpdater] quitAndInstall skipped: Auto updater is disabled.');
}

function getHostUpdateStatus() {
    const currentVersion = electron_1.app.getVersion();
    return {
        currentVersion,
        latestVersion: currentVersion,
        updateAvailable: false,
    };
}

function applyHostUpdate() {
    console.log('[AutoUpdater] applyHostUpdate skipped: Auto updater is disabled.');
    return false;
}

function headlessQuitAndInstall(downloadedFilePath) {
    console.log('[AutoUpdater] headlessQuitAndInstall skipped: Auto updater is disabled.');
}
