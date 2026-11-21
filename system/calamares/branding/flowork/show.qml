import QtQuick 2.0;
import QtQuick.Layouts 1.3;

Presentation
{
    id: presentation

    Timer {
        interval: 10000
        running: true
        repeat: true
        onTriggered: presentation.goToNextSlide()
    }

    Slide {
        Image {
            id: slide1
            source: "welcome.png"
            anchors.fill: parent
            fillMode: Image.PreserveAspectCrop
        }
    }
}
