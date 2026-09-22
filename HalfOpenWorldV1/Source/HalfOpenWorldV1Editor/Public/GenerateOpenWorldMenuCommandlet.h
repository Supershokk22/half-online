#pragma once

#include "Commandlets/Commandlet.h"
#include "GenerateOpenWorldMenuCommandlet.generated.h"

UCLASS()
class HALFOPENWORLDV1EDITOR_API UGenerateOpenWorldMenuCommandlet final : public UCommandlet
{
    GENERATED_BODY()
public:
    UGenerateOpenWorldMenuCommandlet();
    virtual int32 Main(const FString& Params) override;
};
