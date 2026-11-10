import QtQuick 2.0;
import QtQuick.Layouts 1.3;

Presentation
{
    id: presentation

    Timer {
        interval: 8000
        running: true
        repeat: true
        onTriggered: presentation.goToNextSlide()
    }

    Slide {
        Rectangle {
            anchors.fill: parent
            color: "#060a12"

            ColumnLayout {
                anchors.centerIn: parent
                spacing: 16

                Text {
                    text: "FLOWORK OS 1.0 SOVEREIGN RUST LINUX"
                    color: "#00f2fe"
                    font.family: "JetBrains Mono"
                    font.pixelSize: 22
                    font.bold: true
                    Layout.alignment: Qt.AlignHCenter
                }

                Text {
                    text: "The First Truly Agent-Native Operating System"
                    color: "#ffffff"
                    font.family: "Inter"
                    font.pixelSize: 14
                    Layout.alignment: Qt.AlignHCenter
                }

                Rectangle {
                    width: 320
                    height: 1
                    color: "rgba(0, 242, 254, 0.4)"
                    Layout.alignment: Qt.AlignHCenter
                }

                Text {
                    text: "• Pilar 1: JIT .flowapp Bundle & Landlock LSM Sandboxing\n• Pilar 2: Flowork Ambient Vision (Instant Screen Sight)\n• Pilar 3: FlowFS Local Semantic Vector Search (<15ms)\n• Pilar 4: Sovereign Time-Lock Btrfs Instant Auto-Rollback\n• Pilar 5: Unified Acoustic Suite (Earshot DSP & Speech Engine)\n• Pilar 6: Cross-App Neural Bus Multi-App Chaining"
                    color: "#a0aec0"
                    font.family: "JetBrains Mono"
                    font.pixelSize: 12
                    lineHeight: 1.5
                    Layout.alignment: Qt.AlignHCenter
                }
            }
        }
    }
}
