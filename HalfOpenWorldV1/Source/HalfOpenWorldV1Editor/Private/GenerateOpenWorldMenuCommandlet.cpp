#include "GenerateOpenWorldMenuCommandlet.h"

#include "AssetToolsModule.h"
#include "WidgetBlueprint.h"
#include "WidgetBlueprintFactory.h"
#include "Blueprint/WidgetTree.h"
#include "Components/Border.h"
#include "Components/Button.h"
#include "Components/CanvasPanel.h"
#include "Components/CanvasPanelSlot.h"
#include "Components/TextBlock.h"
#include "EditorAssetLibrary.h"
#include "Kismet2/BlueprintEditorUtils.h"
#include "Kismet2/KismetEditorUtilities.h"

namespace
{
    constexpr TCHAR Path[] = TEXT("/Game/HalfOpenWorld/UI/WBP_OpenWorldMenu");

    UCanvasPanelSlot* Put(UCanvasPanel* Canvas, UWidget* Widget, FVector2D Pos, FVector2D Size)
    {
        UCanvasPanelSlot* Slot = Cast<UCanvasPanelSlot>(Canvas->AddChild(Widget));
        Slot->SetPosition(Pos);
        Slot->SetSize(Size);
        return Slot;
    }

    UTextBlock* Label(UWidgetTree* Tree, UCanvasPanel* Canvas, const TCHAR* Name,
        const TCHAR* Value, FVector2D Pos, FVector2D Size, int32 FontSize, FLinearColor Color)
    {
        UTextBlock* Text = Tree->ConstructWidget<UTextBlock>(UTextBlock::StaticClass(), FName(Name));
        Text->SetText(FText::FromString(Value));
        Text->SetColorAndOpacity(FSlateColor(Color));
        FSlateFontInfo Font = Text->GetFont();
        Font.Size = FontSize;
        Text->SetFont(Font);
        Put(Canvas, Text, Pos, Size);
        return Text;
    }

    void MenuRow(UWidgetTree* Tree, UCanvasPanel* Canvas, const TCHAR* ButtonName,
        const TCHAR* Caption, float Y)
    {
        UButton* Button = Tree->ConstructWidget<UButton>(UButton::StaticClass(), FName(ButtonName));
        Button->SetBackgroundColor(FLinearColor(0.20f, 0.17f, 0.14f, 0.95f));
        Put(Canvas, Button, FVector2D(80.f, Y), FVector2D(350.f, 50.f));
        Label(Tree, Canvas, *FString::Printf(TEXT("%s_Label"), ButtonName), Caption,
            FVector2D(105.f, Y + 11.f), FVector2D(310.f, 32.f), 21,
            FLinearColor(0.94f, 0.86f, 0.70f, 1.f));
    }
}

UGenerateOpenWorldMenuCommandlet::UGenerateOpenWorldMenuCommandlet()
{
    IsClient = false;
    IsEditor = true;
    LogToConsole = true;
}

int32 UGenerateOpenWorldMenuCommandlet::Main(const FString& Params)
{
    if (UEditorAssetLibrary::DoesAssetExist(Path))
    {
        UE_LOG(LogTemp, Display, TEXT("Existing menu preserved: %s"), Path);
        return 0;
    }
    UWidgetBlueprintFactory* Factory = NewObject<UWidgetBlueprintFactory>();
    Factory->ParentClass = UUserWidget::StaticClass();
    FAssetToolsModule& Tools = FModuleManager::LoadModuleChecked<FAssetToolsModule>("AssetTools");
    UWidgetBlueprint* Blueprint = Cast<UWidgetBlueprint>(Tools.Get().CreateAsset(
        TEXT("WBP_OpenWorldMenu"), TEXT("/Game/HalfOpenWorld/UI"), UWidgetBlueprint::StaticClass(), Factory));
    if (!Blueprint || !Blueprint->WidgetTree)
    {
        UE_LOG(LogTemp, Error, TEXT("Failed to create WBP_OpenWorldMenu"));
        return 1;
    }
    UWidgetTree* Tree = Blueprint->WidgetTree;
    UCanvasPanel* Canvas = Tree->ConstructWidget<UCanvasPanel>(UCanvasPanel::StaticClass(), TEXT("RootCanvas"));
    Tree->RootWidget = Canvas;
    UBorder* Panel = Tree->ConstructWidget<UBorder>(UBorder::StaticClass(), TEXT("MenuPanel"));
    Panel->SetBrushColor(FLinearColor(0.035f, 0.03f, 0.028f, 0.94f));
    Put(Canvas, Panel, FVector2D(45.f, 45.f), FVector2D(430.f, 600.f));
    Label(Tree, Canvas, TEXT("Title"), TEXT("HALF OPEN WORLD"),
        FVector2D(80.f, 85.f), FVector2D(370.f, 60.f), 37,
        FLinearColor(0.82f, 0.66f, 0.38f, 1.f));
    Label(Tree, Canvas, TEXT("Subtitle"), TEXT("A new path through Half Sword"),
        FVector2D(82.f, 145.f), FVector2D(340.f, 30.f), 15,
        FLinearColor(0.72f, 0.72f, 0.69f, 1.f));
    MenuRow(Tree, Canvas, TEXT("NewGameButton"), TEXT("NOVO JOGO"), 225.f);
    MenuRow(Tree, Canvas, TEXT("ContinueButton"), TEXT("CONTINUAR"), 290.f);
    MenuRow(Tree, Canvas, TEXT("SettingsButton"), TEXT("CONFIGURACOES"), 355.f);
    MenuRow(Tree, Canvas, TEXT("BackButton"), TEXT("VOLTAR"), 420.f);
    Label(Tree, Canvas, TEXT("Signature"), TEXT("V1 / ASSINADO: SHOKK"),
        FVector2D(82.f, 568.f), FVector2D(330.f, 25.f), 13,
        FLinearColor(0.62f, 0.48f, 0.29f, 1.f));
    FBlueprintEditorUtils::MarkBlueprintAsStructurallyModified(Blueprint);
    FKismetEditorUtilities::CompileBlueprint(Blueprint);
    if (!UEditorAssetLibrary::SaveAsset(Path, false))
    {
        UE_LOG(LogTemp, Error, TEXT("Failed to save %s"), Path);
        return 1;
    }
    UE_LOG(LogTemp, Display, TEXT("Menu widget saved: %s"), Path);
    return 0;
}
